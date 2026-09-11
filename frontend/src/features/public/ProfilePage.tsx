import { useMutation, useQuery } from '@tanstack/react-query'
import {
  ArrowLeft,
  ArrowRight,
  BadgeCheck,
  BriefcaseBusiness,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  Eye,
  ExternalLink,
  FileText,
  Maximize2,
  Send,
  Sparkles,
  X,
} from 'lucide-react'
import { type FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { RatingSummary } from '../../components/RatingSummary'
import { SecureImage } from '../../components/SecureImage'
import { SkillLevel } from '../../components/SkillLevel'
import { ApiError, apiBlob, apiRequest } from '../../lib/api'
import type {
  Portfolio,
  Project,
  ProjectInvitation,
  ProjectValidation,
  PublicCredential,
  Review,
  StudentProfile,
} from '../../lib/types'
import { useAuth } from '../auth/use-auth'

const evidenceTypeLabels: Record<string, string> = {
  visual_poster: '视觉作品',
  data_visualization: '数据可视化',
  code_project: '代码项目',
  document: '内容文档',
  operations_record: '运营执行记录',
}

const positionCategoryLabels: Record<string, string> = {
  design: '设计岗位',
  development: '代码开发岗位',
  data: '数据分析岗位',
  content: '内容创作岗位',
  operations: '运营执行岗位',
  general: '综合协作岗位',
}

async function openPortfolioFile(portfolio: Portfolio) {
  const blob = await apiBlob(portfolio.file_url)
  const url = URL.createObjectURL(blob)
  window.open(url, '_blank', 'noopener,noreferrer')
  window.setTimeout(() => URL.revokeObjectURL(url), 30_000)
}

function credentialForPortfolio(portfolio: Portfolio, credentials: PublicCredential[]) {
  const matches = credentials.filter((credential) => (
    credential.evidence_summary.portfolio_id === portfolio.id
    || (!credential.evidence_summary.portfolio_id && credential.evidence_summary.title === portfolio.title)
  ))
  return matches.find((credential) => credential.status === 'active') || matches[0]
}

function PortfolioArchiveRow({
  portfolio,
  credential,
  onOpen,
}: {
  portfolio: Portfolio
  credential?: PublicCredential
  onOpen: () => void
}) {
  const verificationLabel = credential?.status === 'active'
    ? '人工核验通过'
    : credential?.status === 'revoked'
      ? '核验已撤销'
      : '公开作品'
  return <button type="button" className="profile-portfolio-row" onClick={onOpen} aria-label={`查看作品集：${portfolio.title}`}>
    <span className="profile-portfolio-thumb">
      {portfolio.file_type.startsWith('image/') ? <SecureImage src={portfolio.file_url} alt="" /> : <FileText size={27} />}
    </span>
    <span className="profile-portfolio-copy">
      <span>{evidenceTypeLabels[portfolio.evidence_type] ?? '作品记录'} · {new Date(portfolio.created_at).toLocaleDateString('zh-CN')}</span>
      <strong>{portfolio.title}</strong>
      <small>{portfolio.description || '尚未填写作品说明'}</small>
    </span>
    <span className={`profile-portfolio-state ${credential?.status ?? ''}`}><BadgeCheck size={17} />{verificationLabel}</span>
    <ChevronRight className="profile-portfolio-arrow" size={21} />
  </button>
}

function PortfolioDetailDialog({
  portfolio,
  credential,
  onClose,
}: {
  portfolio: Portfolio
  credential?: PublicCredential
  onClose: () => void
}) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const [zoomed, setZoomed] = useState(false)
  const aiResult = credential?.ai_result ?? credential?.verified_result
  const aiCriteria = aiResult?.criteria ?? []
  const verifiedCriteria = credential?.verified_result.criteria ?? []
  const aiScores = new Map(aiCriteria.map((criterion) => [criterion.criterion, criterion.score]))
  const combinedCriteria = verifiedCriteria.length ? verifiedCriteria : aiCriteria

  useEffect(() => {
    if (dialogRef.current && !dialogRef.current.open) dialogRef.current.showModal()
  }, [])

  function closeDialog() {
    setZoomed(false)
    if (dialogRef.current?.open) dialogRef.current.close()
    onClose()
  }

  return <dialog
    ref={dialogRef}
    className="profile-work-dialog"
    aria-labelledby="profile-work-dialog-title"
    onClose={onClose}
    onCancel={(event) => {
      if (zoomed) {
        event.preventDefault()
        setZoomed(false)
      } else onClose()
    }}
    onClick={(event) => { if (event.target === event.currentTarget) closeDialog() }}
  >
    <header>
      <div><span>{evidenceTypeLabels[portfolio.evidence_type] ?? '作品集档案'}</span><h2 id="profile-work-dialog-title">{portfolio.title}</h2></div>
      <button type="button" aria-label="关闭作品详情" onClick={closeDialog}><X size={22} /></button>
    </header>
    <div className="profile-work-dialog-body">
      <section className="profile-work-showcase" aria-labelledby="profile-work-content-title">
        <div className="profile-work-media">
          {portfolio.file_type.startsWith('image/')
            ? <button type="button" onClick={() => setZoomed(true)} aria-label={`放大查看作品：${portfolio.title}`}><SecureImage src={portfolio.file_url} alt={portfolio.title} /><span><Maximize2 size={16} />放大查看</span></button>
            : <button type="button" className="profile-document-open" onClick={() => void openPortfolioFile(portfolio)}><FileText size={35} /><span>打开作品原文件</span><ExternalLink size={16} /></button>}
        </div>
        <div className="profile-work-copy">
          <div><p className="eyebrow">PORTFOLIO CONTENT</p><h3 id="profile-work-content-title">作品内容</h3><p>{portfolio.description || '尚未填写作品说明'}</p></div>
          <dl className="profile-work-story">
            <div><dt>创作背景</dt><dd>{portfolio.creation_context || '待补充'}</dd></div>
            <div><dt>本人职责</dt><dd>{portfolio.personal_role || '待补充'}</dd></div>
            <div><dt>制作过程</dt><dd>{portfolio.process_description || '待补充'}</dd></div>
            <div><dt>迭代说明</dt><dd>{portfolio.iteration_notes || '待补充'}</dd></div>
          </dl>
        </div>
      </section>

      <section className="profile-combined-review" aria-labelledby="profile-combined-review-title">
        <header><div><p className="eyebrow">AI REVIEW × HUMAN VERIFICATION</p><h3 id="profile-combined-review-title">AI 初评与人工核验</h3></div>{credential && <span className={`profile-verification-badge ${credential.status}`}><BadgeCheck size={17} />{credential.status === 'active' ? '人工核验通过' : '核验已撤销'}</span>}</header>
        {credential ? <>
          <div className="profile-review-flow">
            <article><span><Sparkles size={17} />AI 辅助初评</span><strong>{aiResult?.total_score ?? '—'}<small>/ 100</small></strong><p>作为人工复核的辅助输入，不单独构成认证。</p></article>
            <ArrowRight size={24} />
            <article><span><BadgeCheck size={17} />人工审核</span><strong>{credential.verified_result.total_score ?? '—'}<small>/ 100</small></strong><p>{credential.status === 'active' ? `由 ${credential.issuer} 完成人工核验` : '该核验凭证目前已撤销'}</p></article>
          </div>
          {!!combinedCriteria.length && <div className="profile-rubric-comparison">{combinedCriteria.map((criterion) => <div key={criterion.criterion}>
            <span>{criterion.criterion}</span>
            <small>AI 初评 {aiScores.get(criterion.criterion) ?? '—'} / 4</small>
            <strong>人工确认 {criterion.score} / 4</strong>
          </div>)}</div>}
          <div className="profile-human-note"><span>人工复核说明</span><p>{credential.verified_result.human_review_reason || '人工评审已核对作品、过程说明与答辩记录。'}</p></div>
          <Link className="profile-credential-link" to={`/credentials/${credential.credential_number}`}>查看核验凭证 <ExternalLink size={15} /></Link>
        </> : <div className="profile-review-empty"><Sparkles size={24} /><div><b>尚未完成人工核验</b><p>未核验的 AI 观察不会在公开档案中展示。完成复核后，AI 初评与人工结论会在这里合并呈现。</p></div></div>}
      </section>
    </div>
    {zoomed && portfolio.file_type.startsWith('image/') && <div className="profile-work-zoom">
      <button type="button" aria-label="退出放大查看" onClick={() => setZoomed(false)}><X size={23} />退出放大</button>
      <SecureImage src={portfolio.file_url} alt={portfolio.title} />
    </div>}
  </dialog>
}

function ProjectExperienceCard({ record, review }: { record?: ProjectValidation; review?: Review }) {
  const criteria = record?.criteria_scores ?? review?.criteria_scores ?? {}
  const category = record?.position_category ?? review?.rubric_category ?? 'general'
  const createdAt = record?.created_at ?? review?.created_at
  return <article className="profile-project-experience">
    <header>
      <div><span>{positionCategoryLabels[category] ?? '项目岗位'} · {record?.position_title ?? review?.position_title ?? '综合岗位'}</span><h3>{record?.project_title ?? review?.project_title ?? '项目经历'}</h3></div>
      <span className="profile-project-status"><CheckCircle2 size={16} />已完成并评价</span>
    </header>
    <div className="profile-project-body">
      <div className="profile-project-delivery">
        <div><span>项目交付</span><p>{record?.deliverables || '项目交付物已完成并留档'}</p></div>
        {record?.acceptance_criteria && <div><span>验收依据</span><p>{record.acceptance_criteria}</p></div>}
        {!!record?.required_skills.length && <div><span>关联技能</span><div className="skill-tags">{record.required_skills.map((skill) => <span key={skill}>{skill}</span>)}</div></div>}
      </div>
      {!!Object.keys(criteria).length && <dl className="profile-project-scores">{Object.entries(criteria).map(([criterion, score]) => <div key={criterion}><dt>{criterion}</dt><dd>{score}<small>/5</small></dd></div>)}</dl>}
    </div>
    {review && <footer><div><span>项目方评价</span><blockquote>{review.comment || '项目方已完成评价'}</blockquote></div>{createdAt && <time dateTime={createdAt}><CalendarDays size={15} />{new Date(createdAt).toLocaleDateString('zh-CN')}</time>}</footer>}
  </article>
}

export function ProfilePage() {
  const { id } = useParams()
  const { user } = useAuth()
  const inviteDialogRef = useRef<HTMLDialogElement>(null)
  const [inviteOpen, setInviteOpen] = useState(false)
  const [selectedProjectId, setSelectedProjectId] = useState('')
  const [sentInvitation, setSentInvitation] = useState<ProjectInvitation | null>(null)
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null)
  const profile = useQuery({ queryKey: ['student', id], queryFn: () => apiRequest<StudentProfile>(`/api/v1/profiles/students/${id}`) })
  const reviews = useQuery({ queryKey: ['reviews', id], queryFn: () => apiRequest<Review[]>(`/api/v1/profiles/students/${id}/reviews`) })
  const validations = useQuery({ queryKey: ['project-validations', id], queryFn: () => apiRequest<ProjectValidation[]>(`/api/v1/profiles/students/${id}/project-validations`) })
  const credentials = useQuery({ queryKey: ['verified-credentials', id], queryFn: () => apiRequest<PublicCredential[]>(`/api/v1/profiles/students/${id}/verified-credentials`) })
  const requesterProjects = useQuery({ queryKey: ['my-projects'], queryFn: () => apiRequest<Project[]>('/api/v1/projects/mine'), enabled: user?.role === 'requester' })
  const eligibleProjects = useMemo(() => requesterProjects.data?.filter((project) => project.audit_status === 'approved' && project.lifecycle_status === 'recruiting' && new Date(project.deadline) >= new Date(new Date().toDateString())) ?? [], [requesterProjects.data])
  const activeProjectId = selectedProjectId || (eligibleProjects[0] ? String(eligibleProjects[0].id) : '')
  const activeProject = eligibleProjects.find((project) => String(project.id) === activeProjectId)
  const isOwnPreview = user?.role === 'student' && String(user.id) === id
  const invite = useMutation({
    mutationFn: ({ projectId, positionId, message }: { projectId: number; positionId:number|null; message: string }) => apiRequest<ProjectInvitation>(`/api/v1/projects/${projectId}/invitations`, { method: 'POST', body: JSON.stringify({ student_id: Number(id), ...(positionId ? { position_id:positionId } : {}), message }) }),
    onSuccess: setSentInvitation,
  })

  useEffect(() => {
    const dialog = inviteDialogRef.current
    if (!dialog) return
    if (inviteOpen && !dialog.open) dialog.showModal()
    if (!inviteOpen && dialog.open) dialog.close()
  }, [inviteOpen])

  if (profile.isLoading) return <div className="page-state">读取成长档案…</div>
  if (!profile.data) return <div className="page-state">档案不存在</div>

  const student = profile.data
  const credentialList = credentials.data ?? []
  const reviewList = reviews.data ?? []
  const validationList = validations.data ?? []
  const reviewedProjectIds = new Set(validationList.map((record) => record.project_id))
  const experienceRecords = [
    ...validationList.map((record) => ({ key: `validation-${record.id}`, record, review: reviewList.find((item) => item.project_id === record.project_id) })),
    ...reviewList.filter((review) => !reviewedProjectIds.has(review.project_id)).map((review) => ({ key: `review-${review.id}`, record: undefined, review })),
  ]
  const selectedCredential = selectedPortfolio ? credentialForPortfolio(selectedPortfolio, credentialList) : undefined

  function openInviteDialog() {
    invite.reset()
    setSentInvitation(null)
    setSelectedProjectId(eligibleProjects[0] ? String(eligibleProjects[0].id) : '')
    setInviteOpen(true)
  }

  function closeInviteDialog() {
    setInviteOpen(false)
  }

  function submitInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const positionId = String(form.get('position_id') || '')
    invite.mutate({ projectId: Number(activeProjectId), positionId:positionId ? Number(positionId) : null, message: String(form.get('message') || '') })
  }

  return <section className="profile-page">
    {isOwnPreview && <aside className="own-profile-preview-note"><div><Eye size={19} /><span><b>你的公开档案预览</b><small>这是项目方从技能大厅进入后看到的内容，私密作品不会显示。</small></span></div><Link to="/student"><ArrowLeft size={15} />返回工作台</Link></aside>}
    <header className="profile-hero-header">
      <div className="profile-hero-copy">
        <div className="profile-public-identity"><div className="profile-public-avatar"><strong>{student.display_name.trim().slice(0, 1) || '档'}</strong>{student.avatar_url && <img src={student.avatar_url} alt={`${student.display_name}的头像`} onError={(event) => { event.currentTarget.hidden = true }} />}</div><div><p className="eyebrow">PUBLIC PORTFOLIO · {student.username}</p><h1>{student.display_name}</h1><p>{[student.school, student.college, student.major, student.grade].filter(Boolean).join(' · ')}</p></div></div>
        <blockquote>{student.bio || '这位同学正在用作品和真实项目完善自己的成长档案。'}</blockquote>
      </div>
      {user?.role === 'requester' && <button type="button" className="profile-invite-button" onClick={openInviteDialog}><Send size={18} /><span><b>邀约参与项目</b><small>由学生自主决定是否申请</small></span></button>}
    </header>

    <div className="profile-boundary">公开档案由成长活跃度、公开作品集和项目经历三部分组成。AI 只提供辅助观察，最终核验状态以人工审核记录为准。</div>
    <div className="profile-major-sections">
      <section className="profile-major-section">
        <header className="profile-major-heading"><span>01</span><div><p>GROWTH ACTIVITY</p><h2>成长活跃度</h2></div><small>{student.skills.length} 项技能记录</small></header>
        <div className="profile-growth-list">{student.skills.length ? student.skills.map((skill) => <SkillLevel skill={skill} interactive key={skill.id} />) : <div className="empty-inline">尚未添加技能</div>}</div>
      </section>

      <section className="profile-major-section">
        <header className="profile-major-heading"><span>02</span><div><p>PUBLIC PORTFOLIO</p><h2>公开作品集</h2></div><small>{student.portfolios.length} 份公开作品</small></header>
        <div className="profile-portfolio-list">{student.portfolios.length ? student.portfolios.map((portfolio) => <PortfolioArchiveRow portfolio={portfolio} credential={credentialForPortfolio(portfolio, credentialList)} onOpen={() => setSelectedPortfolio(portfolio)} key={portfolio.id} />) : <div className="empty-inline">没有公开作品；私密作品不会在这里出现</div>}</div>
      </section>

      <section className="profile-major-section">
        <header className="profile-major-heading"><span>03</span><div><p>PROJECT EXPERIENCE</p><h2>项目经历</h2></div><small>{experienceRecords.length} 条项目记录</small></header>
        {!!reviewList.length && <div className="profile-project-overview"><div><span>项目方综合评价</span><p>汇总已完成项目中的技能表现、沟通协作、成果交付和时间管理。</p></div><RatingSummary reviews={reviewList} /></div>}
        <div className="profile-project-list">{experienceRecords.length ? experienceRecords.map((item) => <ProjectExperienceCard record={item.record} review={item.review} key={item.key} />) : <div className="empty-inline">尚无已完成并经过项目方评价的项目经历</div>}</div>
      </section>
    </div>

    {selectedPortfolio && <PortfolioDetailDialog portfolio={selectedPortfolio} credential={selectedCredential} onClose={() => setSelectedPortfolio(null)} />}

    {user?.role === 'requester' && <dialog ref={inviteDialogRef} className="invite-dialog" onClose={() => setInviteOpen(false)} onCancel={() => setInviteOpen(false)} aria-labelledby="invite-dialog-title">
      <header><span><BriefcaseBusiness size={20} /></span><div><p className="eyebrow">PROJECT INVITATION</p><h2 id="invite-dialog-title">邀约 {student.display_name}</h2></div><button type="button" aria-label="关闭邀约窗口" onClick={closeInviteDialog}><X size={20} /></button></header>
      {sentInvitation ? <div className="invite-success"><CheckCircle2 size={35} /><h3>邀约已发送</h3><p>学生会在工作台收到“{sentInvitation.project.title}”的项目邀约，并可自行查看和申请。</p><button type="button" className="primary-button" onClick={closeInviteDialog}>完成</button></div> : requesterProjects.isLoading ? <div className="invite-dialog-state">正在读取可邀约项目…</div> : eligibleProjects.length ? <form onSubmit={submitInvite}>
        <label>选择项目<select name="project_id" value={activeProjectId} onChange={(event) => { setSelectedProjectId(event.target.value); invite.reset() }} required>{eligibleProjects.map((project) => <option value={project.id} key={project.id}>{project.title}</option>)}</select></label>
        {!!activeProject?.positions?.length && <label>邀约岗位<select name="position_id" required><option value="">请选择岗位</option>{activeProject.positions.map((position) => <option value={position.id} key={position.id}>{position.title} · {position.category}</option>)}</select></label>}
        <label>邀约留言<textarea name="message" maxLength={1000} placeholder="简单说明为什么希望邀请这位同学参与项目" /></label>
        <p className="invite-boundary">邀约不会自动录取学生，也不会开放其私密作品；学生查看项目后仍需主动申请。</p>
        {invite.isError && <p className="form-error" role="alert">{invite.error instanceof ApiError ? invite.error.message : '邀约发送失败，请稍后重试'}</p>}
        <div className="invite-dialog-actions"><button type="button" className="secondary-button" onClick={closeInviteDialog}>取消</button><button className="primary-button" disabled={invite.isPending}><Send size={16} />{invite.isPending ? '发送中…' : '发送项目邀约'}</button></div>
      </form> : <div className="invite-dialog-empty"><h3>暂无可邀约项目</h3><p>只有已经审核通过并处于招募中的项目可以发出邀约。</p><Link className="primary-button" to="/requester/new" onClick={closeInviteDialog}>发布新项目</Link></div>}
    </dialog>}
  </section>
}
