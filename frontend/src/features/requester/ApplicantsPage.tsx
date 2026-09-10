import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { SecureImage } from '../../components/SecureImage'
import { apiRequest } from '../../lib/api'
import { statusLabel, verificationLabels } from '../../lib/status'
import type { Application } from '../../lib/types'

export function ApplicantsPage() {
  const { id } = useParams()
  const queryClient = useQueryClient()
  const applicants = useQuery({ queryKey:['applicants', id], queryFn:() => apiRequest<Application[]>(`/api/v1/projects/${id}/applications`) })
  const action = useMutation({
    mutationFn:({ applicationId, operation }:{ applicationId:number; operation:'accept'|'reject' }) => apiRequest(`/api/v1/applications/${applicationId}/${operation}`, { method:'POST' }),
    onSuccess:() => queryClient.invalidateQueries({ queryKey:['applicants', id] }),
  })
  return <section className="workspace-page">
    <p className="eyebrow">AUTHORIZED CANDIDATE FILES</p><h1>申请者管理</h1>
    <p className="page-intro">这里只展示学生主动授权给本项目的作品。AI 初评是辅助信号，最终以人工核验与真实项目表现为准。</p>
    <div className="applicant-list">{applicants.data?.map((application) => <article className="applicant-card" key={application.id}>
      <header><div><span>申请 #{application.id}</span><h2>{application.student?.display_name ?? `学生 ${application.student_id}`}</h2></div><span className="status-chip" data-status={application.status}>{statusLabel(application.status)}</span></header>
      <p className="application-message">“{application.message || '未填写申请留言'}”</p>
      <div className="skill-tags">{application.student?.skills.map((skill) => <span key={skill.id}>{skill.name}</span>)}</div>
      <section><h3>学生授权作品</h3>{application.authorized_portfolios?.length ? <div className="authorized-grid">{application.authorized_portfolios.map((portfolio) => <article className="authorized-work" key={portfolio.id}>
        {portfolio.file_type.startsWith('image/') && <SecureImage src={portfolio.file_url} alt={portfolio.title} />}
        <h4>{portfolio.title}</h4><p>{portfolio.description}</p>
        {portfolio.ai_assessment ? <div className="ai-summary"><span>{portfolio.result_label}</span><b>AI {portfolio.ai_assessment.total_score ?? '—'} / 100</b><small>人工状态：{portfolio.verification_status ? verificationLabels[portfolio.verification_status] : '待人工复核'}</small></div> : <p className="boundary-note">该作品没有可展示的 AI 复评结果。</p>}
      </article>)}</div> : <div className="empty-inline">学生没有为本项目授权作品</div>}</section>
      {application.status === 'pending' && <div className="record-actions"><button className="primary-button" onClick={() => action.mutate({ applicationId:application.id, operation:'accept' })}>录用</button><button onClick={() => action.mutate({ applicationId:application.id, operation:'reject' })}>拒绝</button></div>}
    </article>)}</div>
    {!applicants.isLoading && !applicants.data?.length && <div className="empty-inline">暂时没有项目申请</div>}
  </section>
}
