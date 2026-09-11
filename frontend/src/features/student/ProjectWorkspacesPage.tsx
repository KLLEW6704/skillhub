import { useQuery } from '@tanstack/react-query'
import { ArrowUpRight, CheckCircle2, Clock3 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { apiRequest } from '../../lib/api'
import { statusLabel } from '../../lib/status'
import type { ProjectWorkspace } from '../../lib/types'

export function ProjectWorkspacesPage() {
  const workspaces = useQuery({ queryKey:['my-project-workspaces'], queryFn:() => apiRequest<ProjectWorkspace[]>('/api/v1/project-workspaces/mine') })
  return <section className="workspace-page student-projects-page"><p className="eyebrow">MY PROJECT COLLABORATION</p><h1>项目协作</h1><p className="page-intro">查看参与项目的整体链路，并与项目方同步更新本人或本岗位的事项状态。</p>
    {workspaces.isLoading ? <div className="page-state">正在整理项目协作空间…</div> : workspaces.isError ? <div className="page-state error">{workspaces.error.message}</div> : workspaces.data?.length ? <div className="student-project-grid">{workspaces.data.map((workspace) => <Link to={`/student/projects/${workspace.project.id}`} key={workspace.project.id}><header><span>{statusLabel(workspace.project.lifecycle_status)}</span><ArrowUpRight size={18} /></header><h2>{workspace.project.title}</h2><div className="mini-progress"><i style={{ width:`${workspace.progress.completion_percent}%` }} /></div><footer><span><CheckCircle2 size={15} />{workspace.progress.done} / {workspace.progress.total} 已完成</span><span><Clock3 size={15} />{workspace.progress.in_progress} 处理中</span></footer></Link>)}</div> : <div className="empty-state"><h2>还没有参与中的项目</h2><p>被项目方录用后，项目协作空间会出现在这里。</p><Link to="/projects">浏览项目大厅</Link></div>}
  </section>
}
