import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertCircle, Archive, ChevronDown, Compass, ExternalLink, Eye, FileUp, PencilLine, RefreshCw, SearchX, ShieldCheck, Trash2, UserRound, Workflow } from 'lucide-react'
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
    <div className="report-heading">
      <div><span className="evidence-kicker">AI 量表摘要</span><h4>辅助初评结果</h4></div>
      <div className="assessment-score"><b>{result.total_score ?? '—'}</b><span>/ 100</span></div>
    </div>
    <p className="boundary-note">该结果只用于辅助观察，不是学校官方认证，也不会自动改变权限、项目状态或成长活跃度。</p>
    <div className="rubric-grid">{result.criteria.map((item) => <article className="rubric-card" key={item.criterion}>
      <header><strong>{item.criterion}</strong><span>{item.score} / 4</span></header>
      <div className="rubric-meter" aria-label={`${item.criterion} ${item.score} 分，共 4 分`}><i style={{ width: `${Math.max(0, Math.min(item.score, 4)) * 25}%` }} /></div>
      <ul>{item.evidence.map((evidence, index) => <li key={`${evidence.reference}-${index}`}>
        <p>{evidence.reason || '该项判断来自作品与答辩中的可核查信息。'}</p>
        <small>{evidence.reference}</small>
      </li>)}</ul>
    </article>)}</div>
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
      <div className="assessment-title-group"><span className="evidence-kicker">AI 动态答辩</span><strong>{latest ? assessmentLabels[latest.status] : '尚未评估'}</strong></div>
      {!latest && <button className="secondary-button" onClick={() => create.mutate()} disabled={!portfolio.ai_supported || !portfolio.ai_processing_consent_at || create.isPending}>发起 AI 观察</button>}
      {latest?.status === 'failed' && <button className="secondary-button" onClick={() => retry.mutate(latest)} disabled={retry.isPending}>重试失败运行</button>}
    </div>
    {!portfolio.ai_supported && <p className="boundary-note">当前格式可以保存为作品证据，但暂不支持 AI 评估。首期只支持 PNG、JPEG、WebP 静态视觉作品。</p>}
    {portfolio.ai_supported && !portfolio.ai_processing_consent_at && <p className="boundary-note">需要先在作品设置中明确同意外部 AI 处理，才能发起评估。</p>}
    {latest?.error && <p className="form-error" role="alert">真实错误：{latest.error}</p>}
    {observation?.structured_result?.observable_facts && <div className="observation-grid">
      <section className="observation-card facts-card">
        <header><span className="assessment-icon"><Eye size={19} /></span><div><span>01 · 已识别</span><h4>作品中的可观察事实</h4><p>只整理图片和作品说明中能够直接核查的内容。</p></div></header>
        <ol className="fact-list">{observation.structured_result.observable_facts.map((fact, index) => <li key={index}>
          <span className="fact-index">{String(index + 1).padStart(2, '0')}</span>
          <div><p>{fact.observation}</p><details><summary>查看证据定位 <ChevronDown size={14} /></summary><small>{fact.evidence.reference}</small></details></div>
        </li>)}</ol>
      </section>
      <section className="observation-card gaps-card">
        <header><span className="assessment-icon"><SearchX size={19} /></span><div><span>02 · 待补充</span><h4>当前证据缺口</h4><p>这些信息无法从现有材料确认，可在答辩中补充。</p></div></header>
        <ul className="gap-list">{observation.structured_result.evidence_gaps?.map((gap) => <li key={gap}><AlertCircle size={17} /><span>{gap}</span></li>)}</ul>
      </section>
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
      <p className="evidence-description">{portfolio.description || '尚未填写作品说明'}</p>
      <dl className="evidence-story-grid">
        <div><dt><span><Compass size={18} /></span>创作背景</dt><dd>{portfolio.creation_context || '待补充'}</dd></div>
        <div><dt><span><UserRound size={18} /></span>本人职责</dt><dd>{portfolio.personal_role || '待补充'}</dd></div>
        <div><dt><span><Workflow size={18} /></span>制作过程</dt><dd>{portfolio.process_description || '待补充'}</dd></div>
        <div><dt><span><RefreshCw size={18} /></span>迭代说明</dt><dd>{portfolio.iteration_notes || '待补充'}</dd></div>
      </dl>
      <div className="portfolio-actions">
        <button className="portfolio-action edit-action" onClick={() => setEditing(!editing)} aria-expanded={editing}><PencilLine size={16} />{editing ? '收起编辑' : '编辑证据'}</button>
        <button className="portfolio-action file-action" onClick={() => openEvidence(portfolio)}><ExternalLink size={16} />查看原文件</button>
        <button className="portfolio-action delete-action" disabled={remove.isPending} onClick={() => confirm('确认删除这份作品证据？此操作不能撤销。') && remove.mutate()}><Trash2 size={16} />{remove.isPending ? '删除中…' : '删除证据'}</button>
      </div>
      {remove.isError && <p className="form-error">{message(remove.error)}</p>}
      {editing && <form className="evidence-edit-form redesigned-edit-form" onSubmit={submitEdit}>
        <div className="edit-form-heading wide-field"><div><span className="evidence-kicker">UPDATE RECORD</span><h3>编辑证据档案</h3></div><p>修改后将保留作品原文件，并更新档案说明与可见范围。</p></div>
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
        <div className="edit-form-actions wide-field"><button className="primary-button" disabled={update.isPending}>{update.isPending ? '保存中…' : '保存修改'}</button><button type="button" className="secondary-button" onClick={() => setEditing(false)}>取消</button></div>
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
    upload.mutate(new FormData(form), { onSuccess: () => { form.reset(); if (preview) URL.revokeObjectURL(preview); setPreview(null) } })
  }

  return <section className="workspace-page evidence-workspace">
    <p className="eyebrow">PORTFOLIO EVIDENCE</p><h1>作品证据</h1>
    <p className="page-intro">先记录背景、职责、过程与迭代，再决定是否授权 AI 或项目方查看。私密作品不会自动公开。</p>
    <p className="boundary-note">AI 只生成可追溯的辅助观察与初评分，不是学校官方认证，也不会自动授予技能称号或录用结果；人工复核和真实项目交付会单独记录。</p>
    <form className="evidence-upload-form evidence-archive-form" onSubmit={submit}>
      <header className="evidence-form-header"><span className="evidence-form-mark"><Archive size={23} /></span><div><span className="evidence-kicker">NEW EVIDENCE RECORD</span><h2>建立证据档案</h2><p>用作品、过程和职责说明，留下可以被核查的实践记录。</p></div><span className="evidence-form-number">01</span></header>
      <div className="evidence-form-body">
        <fieldset className="evidence-form-section">
          <legend><span>01</span><div><b>作品基本信息</b><small>说明这是什么作品，以及它主要对应哪项技能。</small></div></legend>
          <div className="evidence-form-grid">
            <label>主要技能<select name="skill_id" required>{skills.data?.map((skill) => <option value={skill.id} key={skill.id}>{skill.name}</option>)}</select></label>
            <label>作品类型<select name="evidence_type" defaultValue="visual_poster">{evidenceTypes.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
            <label>作品标题<input name="title" required placeholder="例如：迎新季视觉海报" /></label>
            <label>关联技能<select name="related_skill_ids" multiple>{skills.data?.map((skill) => <option value={skill.id} key={skill.id}>{skill.name}</option>)}</select><small>可按住 Ctrl 选择多项</small></label>
            <label className="wide-field">作品说明<textarea name="description" placeholder="简要说明作品目标、内容与最终成果" /></label>
          </div>
        </fieldset>
        <fieldset className="evidence-form-section story-form-section">
          <legend><span>02</span><div><b>证据叙事</b><small>四个维度会作为 AI 追问与人工复核的重要上下文。</small></div></legend>
          <div className="story-input-grid">
            <label><span className="field-title"><Compass size={17} />创作背景</span><textarea name="creation_context" required placeholder="为什么要做这项作品？面向什么场景？" /></label>
            <label><span className="field-title"><UserRound size={17} />本人职责</span><textarea name="personal_role" required placeholder="你具体负责了哪些部分？" /></label>
            <label><span className="field-title"><Workflow size={17} />制作过程</span><textarea name="process_description" required placeholder="从准备到完成经历了哪些步骤？" /></label>
            <label><span className="field-title"><RefreshCw size={17} />迭代说明</span><textarea name="iteration_notes" required placeholder="根据什么反馈做过哪些修改？" /></label>
          </div>
        </fieldset>
        <fieldset className="evidence-form-section">
          <legend><span>03</span><div><b>文件与权限</b><small>选择原始成果，并决定谁能够看到这份证据。</small></div></legend>
          <div className="asset-permission-grid">
            <label className="file-upload-card"><span className="file-upload-icon"><FileUp size={22} /></span><b>选择作品文件</b><small>图片支持 AI 观察；PDF、文档和视频仅保存为证据。</small><input name="file" type="file" required accept=".png,.jpg,.jpeg,.webp,.gif,.pdf,.doc,.docx,.ppt,.pptx,.mp4,.webm" onChange={(event) => { const file = event.target.files?.[0]; if (preview) URL.revokeObjectURL(preview); setPreview(file?.type.startsWith('image/') ? URL.createObjectURL(file) : null) }} /></label>
            <label className="visibility-field"><span className="field-title"><ShieldCheck size={17} />公开范围</span><select name="visibility" defaultValue="private">{Object.entries(visibilityLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select><small>私密作品不会自动出现在技能大厅。</small></label>
            {preview && <img className="local-preview" src={preview} alt="待上传作品预览" />}
            <label className="consent-card check-label wide-field"><input name="ai_processing_consent" type="checkbox" /><span><b>授权 AI 辅助观察</b><small>我明确同意将该作品副本发送给外部 AI 模型处理。AI 结果不会未经人工核验直接公开。</small></span></label>
          </div>
        </fieldset>
      </div>
      <footer className="evidence-form-footer"><p>保存后仍可修改说明和可见范围。</p><button className="primary-button" disabled={upload.isPending}>{upload.isPending ? '正在建立档案…' : '保存作品证据'}</button></footer>
      {upload.isError && <p className="form-error evidence-upload-error" role="alert">{message(upload.error)}</p>}
    </form>
    {!!portfolios.data?.length && <div className="portfolio-list-heading"><div><span className="evidence-kicker">SAVED EVIDENCE</span><h2>已保存的作品证据</h2></div><span>{portfolios.data.length} 份档案</span></div>}
    <div className="evidence-list">{portfolios.data?.map((portfolio) => <PortfolioCard portfolio={portfolio} skills={skills.data ?? []} key={portfolio.id} />)}</div>
    {!portfolios.isLoading && !portfolios.data?.length && <div className="empty-inline">尚未建立作品证据</div>}
  </section>
}
