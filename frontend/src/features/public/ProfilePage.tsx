import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { RatingSummary } from '../../components/RatingSummary'
import { SecureImage } from '../../components/SecureImage'
import { SkillLevel } from '../../components/SkillLevel'
import { apiRequest } from '../../lib/api'
import type { ProjectValidation, PublicCredential, Review, StudentProfile } from '../../lib/types'

export function ProfilePage() {
  const { id } = useParams()
  const profile = useQuery({ queryKey:['student', id], queryFn:() => apiRequest<StudentProfile>(`/api/v1/profiles/students/${id}`) })
  const reviews = useQuery({ queryKey:['reviews', id], queryFn:() => apiRequest<Review[]>(`/api/v1/profiles/students/${id}/reviews`) })
  const validations = useQuery({ queryKey:['project-validations', id], queryFn:() => apiRequest<ProjectValidation[]>(`/api/v1/profiles/students/${id}/project-validations`) })
  const credentials = useQuery({ queryKey:['verified-credentials', id], queryFn:() => apiRequest<PublicCredential[]>(`/api/v1/profiles/students/${id}/verified-credentials`) })
  if (profile.isLoading) return <div className="page-state">读取成长档案…</div>
  if (!profile.data) return <div className="page-state">档案不存在</div>
  const student = profile.data
  return <section className="profile-page"><header><p className="eyebrow">PUBLIC EVIDENCE FILE · {student.username}</p><h1>{student.display_name}</h1><p>{[student.school,student.college,student.major,student.grade].filter(Boolean).join(' · ')}</p><blockquote>{student.bio || '这位同学正在用作品和真实项目完善自己的成长档案。'}</blockquote></header>
    <div className="profile-boundary">本页分开展示成长活跃度、作品证据、AI 辅助初评、人工核验与真实项目记录。成长活跃度不是技能水平，AI 初评也不是官方认证。</div>
    <div className="profile-sections evidence-profile-grid">
      <section><div className="section-title"><span>01</span><h2>成长活跃度</h2></div>{student.skills.length ? student.skills.map((skill) => <SkillLevel skill={skill} key={skill.id} />) : <div className="empty-inline">尚未添加技能</div>}</section>
      <section><div className="section-title"><span>02</span><h2>公开作品证据</h2></div>{student.portfolios.length ? student.portfolios.map((portfolio) => <article className="public-evidence" key={portfolio.id}>{portfolio.file_type.startsWith('image/') && <SecureImage src={portfolio.file_url} alt={portfolio.title} />}<h3>{portfolio.title}</h3><p>{portfolio.description}</p><small>{portfolio.personal_role || '个人职责待补充'}</small></article>) : <div className="empty-inline">没有公开作品；私密作品不会在这里出现</div>}</section>
      <section><div className="section-title"><span>03</span><h2>AI 辅助初评</h2></div><div className="boundary-card"><b>不自动公开未核验结论</b><p>AI 观察结果只在学生授权的流程中提供辅助信号，并始终标注“待人工复核”。</p></div></section>
      <section><div className="section-title"><span>04</span><h2>人工核验</h2></div>{credentials.data?.length ? credentials.data.map((credential) => <Link className="credential-card" to={`/credentials/${credential.credential_number}`} key={credential.credential_number}><span>{credential.name}</span><b>{credential.evidence_summary.title}</b><small>{credential.status === 'revoked' ? '已撤销' : `已核验 · ${credential.credential_number}`}</small></Link>) : <div className="empty-inline">尚无人工核验记录</div>}</section>
      <section><div className="section-title"><span>05</span><h2>真实项目记录</h2></div>{validations.data?.length ? validations.data.map((record) => <article className="validation-card" key={record.id}><h3>{record.project_title}</h3><div className="skill-tags">{record.required_skills.map((skill) => <span key={skill}>{skill}</span>)}</div><p>{record.deliverables || '交付物记录已保存'}</p><small>{new Date(record.created_at).toLocaleDateString()} · 项目方验收记录</small></article>) : <div className="empty-inline">尚无真实项目验证记录</div>}</section>
      <section><div className="section-title"><span>06</span><h2>项目方评价</h2></div><RatingSummary reviews={reviews.data || []} />{reviews.data?.map((review) => <blockquote className="review-quote" key={review.id}>{review.comment || '项目评价已记录'}</blockquote>)}</section>
    </div>
  </section>
}
