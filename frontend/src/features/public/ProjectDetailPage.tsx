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
  const project = useQuery({ queryKey: ['project', id], queryFn: () => apiRequest<Project>(`/api/v1/projects/${id}`) })
  const portfolios = useQuery({ queryKey: ['portfolios'], queryFn: () => apiRequest<Portfolio[]>('/api/v1/portfolios'), enabled: user?.role === 'student' })
  const apply = useMutation({ mutationFn: (payload: unknown) => apiRequest(`/api/v1/projects/${id}/applications`, { method: 'POST', body: JSON.stringify(payload) }) })

  if (project.isLoading) return <div className="page-state">读取项目档案…</div>
  if (!project.data) return <div className="page-state">项目不存在</div>

  const data = project.data
  const expired = new Date(data.deadline) < new Date()

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    apply.mutate({ message: form.get('message'), portfolio_ids: form.getAll('portfolio_ids').map(Number) })
  }

  return <section className="detail-page project-detail-page">
    <Link className="back-link" to="/projects"><ArrowLeft size={16} />返回项目大厅</Link>
    <div className="detail-grid project-detail-layout">
      <article className="project-detail-content">
        <p className="eyebrow">PROJECT FILE · #{data.id}</p>
        <h1>{data.title}</h1>
        <div className="skill-tags">{data.required_skills.map((skill) => <span key={skill}>{skill}</span>)}</div>
        <h2>项目说明</h2>
        <p className="detail-copy">{data.description}</p>
        <h2>约定交付物</h2>
        <p className="detail-copy">{data.deliverables || '项目方尚未补充交付物'}</p>
        <h2>验收标准</h2>
        <p className="detail-copy">{data.acceptance_criteria || '项目方尚未补充验收标准'}</p>
      </article>

      <section className="project-recruitment" aria-labelledby="recruitment-title">
        <header className="project-recruitment-heading">
          <div><p className="eyebrow">RECRUITMENT FILE</p><h2 id="recruitment-title">招募档案</h2><p>确认项目信息后，填写申请留言并选择愿意授权给项目方查看的作品。</p></div>
          <dl className="project-recruitment-meta">
            <div><dt>项目分类</dt><dd>{data.category}</dd></div>
            <div><dt>截止日期</dt><dd><Calendar size={16} />{data.deadline}</dd></div>
            <div><dt>项目条件</dt><dd>{data.budget ? `¥ ${data.budget}` : '志愿实践'}</dd></div>
          </dl>
        </header>

        {user?.role === 'student' && !expired ? <form className="application-form project-application-form" onSubmit={submit}>
          <label className="project-message-field"><span>申请留言</span><textarea name="message" placeholder="说明相关经验、申请原因与可投入时间" /></label>
          <fieldset className="project-evidence-field">
            <legend>主动授权给项目方的作品</legend>
            <div className="project-evidence-list">{portfolios.data?.length ? portfolios.data.map((portfolio) => <label className="check-label" key={portfolio.id}><input type="checkbox" name="portfolio_ids" value={portfolio.id} />{portfolio.title}</label>) : <p className="empty-inline">暂无可授权作品，也可以不选择作品直接提交申请。</p>}</div>
            <small>只有主动勾选的作品会向项目方开放，其他私密作品不会泄露。</small>
          </fieldset>
          <div className="project-apply-footer">
            <p>提交后，项目方可以查看你的申请留言和已授权作品。</p>
            <button className="primary-button" disabled={apply.isPending || apply.isSuccess}><Send size={16} />{apply.isSuccess ? '申请已提交' : apply.isPending ? '提交中…' : '申请加入项目'}</button>
          </div>
        </form> : <div className="closed-note project-recruitment-closed">{expired ? '申请已截止' : user ? '当前身份不可申请' : '登录学生账号后可提交申请'}</div>}
        {apply.isError && <p className="form-error project-application-error">{apply.error.message}</p>}
      </section>
    </div>
  </section>
}
