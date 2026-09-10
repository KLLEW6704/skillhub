import { useMutation, useQuery } from '@tanstack/react-query'
import { BriefcaseBusiness, CheckCircle2, Send, X } from 'lucide-react'
import { type FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { RatingSummary } from '../../components/RatingSummary'
import { SecureImage } from '../../components/SecureImage'
import { SkillLevel } from '../../components/SkillLevel'
import { ApiError, apiRequest } from '../../lib/api'
import type { Project, ProjectInvitation, ProjectValidation, PublicCredential, Review, StudentProfile } from '../../lib/types'
import { useAuth } from '../auth/use-auth'

export function ProfilePage() {
  const { id } = useParams()
  const { user } = useAuth()
  const dialogRef = useRef<HTMLDialogElement>(null)
  const [inviteOpen, setInviteOpen] = useState(false)
  const [selectedProjectId, setSelectedProjectId] = useState('')
  const [sentInvitation, setSentInvitation] = useState<ProjectInvitation | null>(null)
  const profile = useQuery({ queryKey: ['student', id], queryFn: () => apiRequest<StudentProfile>(`/api/v1/profiles/students/${id}`) })
  const reviews = useQuery({ queryKey: ['reviews', id], queryFn: () => apiRequest<Review[]>(`/api/v1/profiles/students/${id}/reviews`) })
  const validations = useQuery({ queryKey: ['project-validations', id], queryFn: () => apiRequest<ProjectValidation[]>(`/api/v1/profiles/students/${id}/project-validations`) })
  const credentials = useQuery({ queryKey: ['verified-credentials', id], queryFn: () => apiRequest<PublicCredential[]>(`/api/v1/profiles/students/${id}/verified-credentials`) })
  const requesterProjects = useQuery({ queryKey: ['my-projects'], queryFn: () => apiRequest<Project[]>('/api/v1/projects/mine'), enabled: user?.role === 'requester' })
  const eligibleProjects = useMemo(() => requesterProjects.data?.filter((project) => project.audit_status === 'approved' && project.lifecycle_status === 'recruiting' && new Date(project.deadline) >= new Date(new Date().toDateString())) ?? [], [requesterProjects.data])
  const activeProjectId = selectedProjectId || (eligibleProjects[0] ? String(eligibleProjects[0].id) : '')
  const invite = useMutation({
    mutationFn: ({ projectId, message }: { projectId: number; message: string }) => apiRequest<ProjectInvitation>(`/api/v1/projects/${projectId}/invitations`, { method: 'POST', body: JSON.stringify({ student_id: Number(id), message }) }),
    onSuccess: setSentInvitation,
  })

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    if (inviteOpen && !dialog.open) dialog.showModal()
    if (!inviteOpen && dialog.open) dialog.close()
  }, [inviteOpen])

  if (profile.isLoading) return <div className="page-state">读取成长档案…</div>
  if (!profile.data) return <div className="page-state">档案不存在</div>

  const student = profile.data
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
    invite.mutate({ projectId: Number(activeProjectId), message: String(form.get('message') || '') })
  }

  return <section className="profile-page">
    <header className="profile-hero-header">
      <div className="profile-hero-copy">
        <div className="profile-public-identity"><div className="profile-public-avatar"><strong>{student.display_name.trim().slice(0, 1) || '档'}</strong>{student.avatar_url && <img src={student.avatar_url} alt={`${student.display_name}的头像`} onError={(event) => { event.currentTarget.hidden = true }} />}</div><div><p className="eyebrow">PUBLIC EVIDENCE FILE · {student.username}</p><h1>{student.display_name}</h1><p>{[student.school, student.college, student.major, student.grade].filter(Boolean).join(' · ')}</p></div></div>
        <blockquote>{student.bio || '这位同学正在用作品和真实项目完善自己的成长档案。'}</blockquote>
      </div>
      {user?.role === 'requester' && <button type="button" className="profile-invite-button" onClick={openInviteDialog}><Send size={18} /><span><b>邀约参与项目</b><small>由学生自主决定是否申请</small></span></button>}
    </header>

    <div className="profile-boundary">本页分开展示成长活跃度、作品证据、AI 辅助初评、人工核验与真实项目记录。成长活跃度不是技能水平，AI 初评也不是官方认证。</div>
    <div className="profile-sections evidence-profile-grid">
      <section><div className="section-title"><span>01</span><h2>成长活跃度</h2></div>{student.skills.length ? student.skills.map((skill) => <SkillLevel skill={skill} key={skill.id} />) : <div className="empty-inline">尚未添加技能</div>}</section>
      <section><div className="section-title"><span>02</span><h2>公开作品证据</h2></div>{student.portfolios.length ? student.portfolios.map((portfolio) => <article className="public-evidence" key={portfolio.id}>{portfolio.file_type.startsWith('image/') && <SecureImage src={portfolio.file_url} alt={portfolio.title} />}<h3>{portfolio.title}</h3><p>{portfolio.description}</p><small>{portfolio.personal_role || '个人职责待补充'}</small></article>) : <div className="empty-inline">没有公开作品；私密作品不会在这里出现</div>}</section>
      <section><div className="section-title"><span>03</span><h2>AI 辅助初评</h2></div><div className="boundary-card"><b>不自动公开未核验结论</b><p>AI 观察结果只在学生授权的流程中提供辅助信号，并始终标注“待人工复核”。</p></div></section>
      <section><div className="section-title"><span>04</span><h2>人工核验</h2></div>{credentials.data?.length ? credentials.data.map((credential) => <Link className="credential-card" to={`/credentials/${credential.credential_number}`} key={credential.credential_number}><span>{credential.name}</span><b>{credential.evidence_summary.title}</b><small>{credential.status === 'revoked' ? '已撤销' : `已核验 · ${credential.credential_number}`}</small></Link>) : <div className="empty-inline">尚无人工核验记录</div>}</section>
      <section><div className="section-title"><span>05</span><h2>真实项目记录</h2></div>{validations.data?.length ? validations.data.map((record) => <article className="validation-card" key={record.id}><h3>{record.project_title}</h3><div className="skill-tags">{record.required_skills.map((skill) => <span key={skill}>{skill}</span>)}</div><p>{record.deliverables || '交付物记录已保存'}</p><small>{new Date(record.created_at).toLocaleDateString()} · 项目方验收记录</small></article>) : <div className="empty-inline">尚无真实项目验证记录</div>}</section>
      <section><div className="section-title"><span>06</span><h2>项目方评价</h2></div><RatingSummary reviews={reviews.data || []} />{reviews.data?.map((review) => <blockquote className="review-quote" key={review.id}>{review.comment || '项目评价已记录'}</blockquote>)}</section>
    </div>

    {user?.role === 'requester' && <dialog ref={dialogRef} className="invite-dialog" onClose={() => setInviteOpen(false)} onCancel={() => setInviteOpen(false)} aria-labelledby="invite-dialog-title">
      <header><span><BriefcaseBusiness size={20} /></span><div><p className="eyebrow">PROJECT INVITATION</p><h2 id="invite-dialog-title">邀约 {student.display_name}</h2></div><button type="button" aria-label="关闭邀约窗口" onClick={closeInviteDialog}><X size={20} /></button></header>
      {sentInvitation ? <div className="invite-success"><CheckCircle2 size={35} /><h3>邀约已发送</h3><p>学生会在工作台收到“{sentInvitation.project.title}”的项目邀约，并可自行查看和申请。</p><button type="button" className="primary-button" onClick={closeInviteDialog}>完成</button></div> : requesterProjects.isLoading ? <div className="invite-dialog-state">正在读取可邀约项目…</div> : eligibleProjects.length ? <form onSubmit={submitInvite}>
        <label>选择项目<select name="project_id" value={activeProjectId} onChange={(event) => { setSelectedProjectId(event.target.value); invite.reset() }} required>{eligibleProjects.map((project) => <option value={project.id} key={project.id}>{project.title}</option>)}</select></label>
        <label>邀约留言<textarea name="message" maxLength={1000} placeholder="简单说明为什么希望邀请这位同学参与项目" /></label>
        <p className="invite-boundary">邀约不会自动录取学生，也不会开放其私密作品；学生查看项目后仍需主动申请。</p>
        {invite.isError && <p className="form-error" role="alert">{invite.error instanceof ApiError ? invite.error.message : '邀约发送失败，请稍后重试'}</p>}
        <div className="invite-dialog-actions"><button type="button" className="secondary-button" onClick={closeInviteDialog}>取消</button><button className="primary-button" disabled={invite.isPending}><Send size={16} />{invite.isPending ? '发送中…' : '发送项目邀约'}</button></div>
      </form> : <div className="invite-dialog-empty"><h3>暂无可邀约项目</h3><p>只有已经审核通过并处于招募中的项目可以发出邀约。</p><Link className="primary-button" to="/requester/new" onClick={closeInviteDialog}>发布新项目</Link></div>}
    </dialog>}
  </section>
}
