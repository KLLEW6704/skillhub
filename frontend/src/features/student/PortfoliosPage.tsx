import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { SecureImage } from '../../components/SecureImage'
import { apiBlob, apiRequest } from '../../lib/api'
import { assessmentLabels, visibilityLabels } from '../../lib/status'
import type { AssessmentRun, Portfolio, Skill } from '../../lib/types'

const evidenceTypes = [
  ['visual_poster', '视觉海报'], ['data_visualization', '数据可视化'], ['document', '文档'], ['other', '其他作品'],
]
const evidenceTypeLabels = Object.fromEntries(evidenceTypes) as Record<string, string>

function message(error: unknown) { return error instanceof Error ? error.message : '操作失败，请稍后重试' }

async function openEvidence(portfolio: Portfolio) {
  const blob = await apiBlob(portfolio.file_url)
  const url = URL.createObjectURL(blob)
  window.open(url, '_blank', 'noopener,noreferrer')
  window.setTimeout(() => URL.revokeObjectURL(url), 30_000)
}

function RubricReport({ run }: { run: AssessmentRun }) {
  const result = run.structured_result
  if (!result?.criteria) return null
  return <section className="assessment-report" aria-label="AI 辅助初评报告">
    <div className="report-heading"><span>AI 辅助初评、待人工复核</span><b>{result.total_score ?? '—'} / 100</b></div>
    <p className="boundary-note">该结果只用于辅助观察，不是学校官方认证，也不会自动改变权限、项目状态或成长活跃度。</p>
    {result.criteria.map((item) => <article className="rubric-row" key={item.criterion}>
      <div><strong>{item.criterion}</strong><span>{item.score} / 4</span></div>
      {item.evidence.map((evidence, index) => <p key={`${evidence.reference}-${index}`}>{evidence.reference}：{evidence.reason}</p>)}
    </article>)}
  </section>
}

function PortfolioAssessment({ portfolio }: { portfolio: Portfolio }) {
  const queryClient = useQueryClient()
  const runs = useQuery({
    queryKey: ['assessments', portfolio.id],
    queryFn: () => apiRequest<AssessmentRun[]>(`/api/v1/portfolios/${portfolio.id}/assessments`),
  })
  const create = useMutation({
    mutationFn: () => apiRequest<AssessmentRun>(`/api/v1/portfolios/${portfolio.id}/assessments`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['assessments', portfolio.id] }),
  })
  const answer = useMutation({
    mutationFn: ({ run, answers }: { run: AssessmentRun; answers: Array<{ question_id: number; answer: string }> }) =>
      apiRequest<AssessmentRun>(`/api/v1/assessments/${run.run_number}/answers`, { method: 'POST', body: JSON.stringify({ answers }) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['assessments', portfolio.id] }),
  })
  const retry = useMutation({
    mutationFn: (run: AssessmentRun) => apiRequest<AssessmentRun>(`/api/v1/assessments/${run.run_number}/retry`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['assessments', portfolio.id] }),
  })
  const allRuns = runs.data ?? []
  const latest = allRuns[0]
  const observation = allRuns.find((run) => run.stage === 'observation' && run.status === 'succeeded')
  const reassessment = allRuns.find((run) => run.stage === 'reassessment')

  function submitAnswers(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!observation) return
    const data = new FormData(event.currentTarget)
    const answers = observation.questions.map((question) => ({
      question_id: question.id,
      answer: String(data.get(`answer_${question.id}`) ?? ''),
    }))
    answer.mutate({ run: observation, answers })
  }

  return <div className="assessment-panel">
    <div className="assessment-panel-heading">
      <div><span className="evidence-kicker">AI 动态答辩</span><strong>{latest ? assessmentLabels[latest.status] : '尚未评估'}</strong></div>
      {!latest && <button className="secondary-button" onClick={() => create.mutate()} disabled={!portfolio.ai_supported || !portfolio.ai_processing_consent_at || create.isPending}>发起 AI 观察</button>}
      {latest?.status === 'failed' && <button className="secondary-button" onClick={() => retry.mutate(latest)} disabled={retry.isPending}>重试失败运行</button>}
    </div>
    {!portfolio.ai_supported && <p className="boundary-note">当前格式可以保存为作品证据，但暂不支持 AI 评估。首期只支持 PNG、JPEG、WebP 静态视觉作品。</p>}
    {portfolio.ai_supported && !portfolio.ai_processing_consent_at && <p className="boundary-note">需要先在作品设置中明确同意外部 AI 处理，才能发起评估。</p>}
    {latest?.error && <p className="form-error" role="alert">真实错误：{latest.error}</p>}
    {observation?.structured_result?.observable_facts && <div className="observation-grid">
      <section><h4>可观察事实</h4>{observation.structured_result.observable_facts.map((fact, index) => <p key={index}>{fact.observation} <small>依据：{fact.evidence.reference}</small></p>)}</section>
      <section><h4>证据缺口</h4>{observation.structured_result.evidence_gaps?.map((gap) => <p key={gap}>{gap}</p>)}</section>
    </div>}
    {observation && !reassessment && <form className="defense-form" onSubmit={submitAnswers}>
      <h4>回答 3 个针对性问题</h4>
      {observation.questions.map((question) => <label key={question.id}><span>{question.position}. {question.text}</span><small>针对：{question.targets_gap}</small><textarea name={`answer_${question.id}`} required defaultValue={question.answer ?? ''} /></label>)}
      <button className="primary-button" disabled={answer.isPending}>{answer.isPending ? '复评中…' : '提交答辩并复评'}</button>
    </form>}
    {answer.isError && <p className="form-error">{message(answer.error)}</p>}
    {create.isError && <p className="form-error">{message(create.error)}</p>}
    {reassessment && <RubricReport run={reassessment} />}
  </div>
}

function PortfolioCard({ portfolio, skills }: { portfolio: Portfolio; skills: Skill[] }) {
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState(false)
  const update = useMutation({
    mutationFn: (payload: unknown) => apiRequest<Portfolio>(`/api/v1/portfolios/${portfolio.id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    onSuccess: () => { setEditing(false); queryClient.invalidateQueries({ queryKey: ['portfolios'] }) },
  })
  const remove = useMutation({
    mutationFn: () => apiRequest<void>(`/api/v1/portfolios/${portfolio.id}`, { method: 'DELETE' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['portfolios'] }),
  })

  function submitEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const data = new FormData(form)
    update.mutate({
      title: data.get('title'), description: data.get('description'), evidence_type: data.get('evidence_type'),
      creation_context: data.get('creation_context'), personal_role: data.get('personal_role'),
      process_description: data.get('process_description'), iteration_notes: data.get('iteration_notes'),
      visibility: data.get('visibility'), related_skill_ids: data.getAll('related_skill_ids').map(Number),
      ai_processing_consent: data.get('ai_processing_consent') === 'on',
    })
  }

  return <article className="evidence-card">
    <div className="evidence-media">{portfolio.file_type.startsWith('image/') ? <SecureImage src={portfolio.file_url} alt={portfolio.title} /> : <button className="document-preview" onClick={() => openEvidence(portfolio)}>打开作品文件</button>}</div>
    <div className="evidence-body">
      <div className="record-heading"><div><span className="evidence-kicker">{evidenceTypeLabels[portfolio.evidence_type] ?? portfolio.evidence_type}</span><h2>{portfolio.title}</h2></div><span className={`status-chip ${portfolio.visibility}`}>{visibilityLabels[portfolio.visibility]}</span></div>
      <p>{portfolio.description || '尚未填写作品说明'}</p>
      <dl className="evidence-details"><div><dt>创作背景</dt><dd>{portfolio.creation_context || '待补充'}</dd></div><div><dt>本人职责</dt><dd>{portfolio.personal_role || '待补充'}</dd></div><div><dt>制作过程</dt><dd>{portfolio.process_description || '待补充'}</dd></div><div><dt>迭代说明</dt><dd>{portfolio.iteration_notes || '待补充'}</dd></div></dl>
      <div className="record-actions"><button onClick={() => setEditing(!editing)}>{editing ? '取消编辑' : '编辑证据'}</button><button onClick={() => openEvidence(portfolio)}>查看原文件</button><button className="danger-button" onClick={() => confirm('确认删除这份作品证据？此操作不能撤销。') && remove.mutate()}>删除</button></div>
      {remove.isError && <p className="form-error">{message(remove.error)}</p>}
      {editing && <form className="evidence-edit-form" onSubmit={submitEdit}>
        <label>作品标题<input name="title" defaultValue={portfolio.title} required /></label>
        <label>作品说明<textarea name="description" defaultValue={portfolio.description ?? ''} /></label>
        <label>作品类型<select name="evidence_type" defaultValue={portfolio.evidence_type}>{evidenceTypes.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
        <label>创作背景<textarea name="creation_context" defaultValue={portfolio.creation_context ?? ''} /></label>
        <label>本人职责<textarea name="personal_role" defaultValue={portfolio.personal_role ?? ''} /></label>
        <label>制作过程<textarea name="process_description" defaultValue={portfolio.process_description ?? ''} /></label>
        <label>迭代说明<textarea name="iteration_notes" defaultValue={portfolio.iteration_notes ?? ''} /></label>
        <label>公开范围<select name="visibility" defaultValue={portfolio.visibility}>{Object.entries(visibilityLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
        <label>关联技能<select name="related_skill_ids" multiple defaultValue={portfolio.related_skill_ids.map(String)}>{skills.map((skill) => <option value={skill.id} key={skill.id}>{skill.name}</option>)}</select></label>
        <label className="check-label"><input name="ai_processing_consent" type="checkbox" defaultChecked={Boolean(portfolio.ai_processing_consent_at)} />我明确同意将该作品副本发送给外部 AI 模型处理</label>
        <button className="primary-button" disabled={update.isPending}>保存证据</button>
        {update.isError && <p className="form-error">{message(update.error)}</p>}
      </form>}
      <PortfolioAssessment portfolio={portfolio} />
    </div>
  </article>
}

export function PortfoliosPage() {
  const queryClient = useQueryClient()
  const [preview, setPreview] = useState<string | null>(null)
  const portfolios = useQuery({ queryKey: ['portfolios'], queryFn: () => apiRequest<Portfolio[]>('/api/v1/portfolios') })
  const skills = useQuery({ queryKey: ['my-skills'], queryFn: () => apiRequest<Skill[]>('/api/v1/skills') })
  const upload = useMutation({
    mutationFn: (body: FormData) => apiRequest<Portfolio>('/api/v1/portfolios', { method: 'POST', body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['portfolios'] }),
  })

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    upload.mutate(new FormData(form), { onSuccess: () => { form.reset(); setPreview(null) } })
  }

  return <section className="workspace-page evidence-workspace">
    <p className="eyebrow">PORTFOLIO EVIDENCE</p><h1>作品证据</h1>
    <p className="page-intro">先记录背景、职责、过程与迭代，再决定是否授权 AI 或项目方查看。私密作品不会自动公开。</p>
    <p className="boundary-note">AI 只生成可追溯的辅助观察与初评分，不是学校官方认证，也不会自动授予技能称号或录用结果；人工复核和真实项目交付会单独记录。</p>
    <form className="evidence-upload-form" onSubmit={submit}>
      <div className="form-section-heading"><span>01</span><div><h2>建立证据档案</h2><p>PNG、JPEG、WebP 支持 AI 观察；PDF、文档和视频可以保存，但暂不进行 AI 评估。</p></div></div>
      <label>主要技能<select name="skill_id" required>{skills.data?.map((skill) => <option value={skill.id} key={skill.id}>{skill.name}</option>)}</select></label>
      <label>关联技能<select name="related_skill_ids" multiple>{skills.data?.map((skill) => <option value={skill.id} key={skill.id}>{skill.name}</option>)}</select></label>
      <label>作品标题<input name="title" required /></label>
      <label>作品类型<select name="evidence_type" defaultValue="visual_poster">{evidenceTypes.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
      <label className="wide-field">作品说明<textarea name="description" /></label>
      <label>创作背景<textarea name="creation_context" required /></label>
      <label>本人职责<textarea name="personal_role" required /></label>
      <label>制作过程<textarea name="process_description" required /></label>
      <label>迭代说明<textarea name="iteration_notes" required /></label>
      <label>公开范围<select name="visibility" defaultValue="private">{Object.entries(visibilityLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
      <label>上传文件<input name="file" type="file" required accept=".png,.jpg,.jpeg,.webp,.gif,.pdf,.doc,.docx,.ppt,.pptx,.mp4,.webm" onChange={(event) => { const file = event.target.files?.[0]; setPreview(file?.type.startsWith('image/') ? URL.createObjectURL(file) : null) }} /></label>
      {preview && <img className="local-preview" src={preview} alt="待上传作品预览" />}
      <label className="check-label wide-field"><input name="ai_processing_consent" type="checkbox" />我明确同意将该作品副本发送给外部 AI 模型处理</label>
      <button className="primary-button" disabled={upload.isPending}>{upload.isPending ? '上传中…' : '保存作品证据'}</button>
      {upload.isError && <p className="form-error wide-field" role="alert">{message(upload.error)}</p>}
    </form>
    <div className="evidence-list">{portfolios.data?.map((portfolio) => <PortfolioCard portfolio={portfolio} skills={skills.data ?? []} key={portfolio.id} />)}</div>
    {!portfolios.isLoading && !portfolios.data?.length && <div className="empty-inline">尚未建立作品证据</div>}
  </section>
}
