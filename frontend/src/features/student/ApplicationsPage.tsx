import { useQuery } from '@tanstack/react-query'
import { ArrowUpRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { apiRequest } from '../../lib/api'
import { statusLabel } from '../../lib/status'
import type { Application } from '../../lib/types'

export function ApplicationsPage() {
  const applications = useQuery({ queryKey:['my-apps'], queryFn:() => apiRequest<Application[]>('/api/v1/applications/mine') })
  return <section className="workspace-page"><p className="eyebrow">MY APPLICATIONS</p><h1>我的申请</h1><div className="application-records">{applications.data?.map((application) => {
    const isMember = application.status === 'accepted' || application.status === 'finished'
    return <article className="record-item application-record" key={application.id}><div><span>{application.position?.title || '综合岗位'}</span><b>{application.project?.title || `项目 #${application.project_id}`}</b><small>{statusLabel(application.status)}</small></div><Link to={isMember ? `/student/projects/${application.project_id}` : `/projects/${application.project_id}`}>{isMember ? '进入协作空间' : '查看项目'}<ArrowUpRight size={16} /></Link></article>
  })}</div>{!applications.isLoading && !applications.data?.length && <div className="empty-inline">还没有提交过项目申请</div>}</section>
}
