import { useMutation, useQuery } from '@tanstack/react-query'
import { ArrowLeft, Calendar, Send } from 'lucide-react'
import type { FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { apiRequest } from '../../lib/api'
import type { Portfolio, Project } from '../../lib/types'
import { useAuth } from '../auth/use-auth'

export function ProjectDetailPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const project = useQuery({ queryKey:['project', id], queryFn:() => apiRequest<Project>(`/api/v1/projects/${id}`) })
  const portfolios = useQuery({ queryKey:['portfolios'], queryFn:() => apiRequest<Portfolio[]>('/api/v1/portfolios'), enabled:user?.role === 'student' })
  const apply = useMutation({ mutationFn:(payload:unknown) => apiRequest(`/api/v1/projects/${id}/applications`, { method:'POST', body:JSON.stringify(payload) }) })
  if (project.isLoading) return <div className="page-state">读取项目档案…</div>
  if (!project.data) return <div className="page-state">项目不存在</div>
  const data = project.data
  const expired = new Date(data.deadline) < new Date()
  function submit(event:FormEvent<HTMLFormElement>) { event.preventDefault(); const form = new FormData(event.currentTarget); apply.mutate({ message:form.get('message'), portfolio_ids:form.getAll('portfolio_ids').map(Number) }) }
  return <section className="detail-page"><Link className="back-link" to="/projects"><ArrowLeft size={16} />返回项目大厅</Link><div className="detail-grid"><article><p className="eyebrow">PROJECT FILE · #{data.id}</p><h1>{data.title}</h1><div className="skill-tags">{data.required_skills.map((skill) => <span key={skill}>{skill}</span>)}</div><h2>项目说明</h2><p className="detail-copy">{data.description}</p><h2>约定交付物</h2><p className="detail-copy">{data.deliverables || '项目方尚未补充交付物'}</p><h2>验收标准</h2><p className="detail-copy">{data.acceptance_criteria || '项目方尚未补充验收标准'}</p></article><aside className="project-aside"><span>招募档案</span><dl><dt>项目分类</dt><dd>{data.category}</dd><dt>截止日期</dt><dd><Calendar size={15} />{data.deadline}</dd><dt>项目条件</dt><dd>{data.budget ? `¥ ${data.budget}` : '志愿实践'}</dd></dl>{user?.role === 'student' && !expired ? <form className="application-form" onSubmit={submit}><label>申请留言<textarea name="message" placeholder="说明相关经验与可投入时间" /></label><fieldset><legend>主动授权给项目方的作品</legend>{portfolios.data?.map((portfolio) => <label className="check-label" key={portfolio.id}><input type="checkbox" name="portfolio_ids" value={portfolio.id} />{portfolio.title}</label>)}<small>不勾选的私密作品不会向项目方泄露。</small></fieldset><button className="primary-button" disabled={apply.isPending || apply.isSuccess}><Send size={16} />{apply.isSuccess ? '申请已提交' : apply.isPending ? '提交中…' : '申请加入项目'}</button></form> : <div className="closed-note">{expired ? '申请已截止' : user ? '当前身份不可申请' : '登录后可提交申请'}</div>}{apply.isError && <p className="form-error">{apply.error.message}</p>}</aside></div></section>
}
