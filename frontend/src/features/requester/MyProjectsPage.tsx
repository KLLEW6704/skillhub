import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowUpRight, UsersRound } from 'lucide-react'
import { Link } from 'react-router-dom'
import { apiRequest } from '../../lib/api'
import { statusLabel } from '../../lib/status'
import type { Project } from '../../lib/types'

export function MyProjectsPage() {
  const queryClient = useQueryClient()
  const projects = useQuery({ queryKey:['my-projects'], queryFn:() => apiRequest<Project[]>('/api/v1/projects/mine') })
  const move = useMutation({ mutationFn:({ id, action }:{id:number; action:string}) => apiRequest(`/api/v1/projects/${id}/${action}`, { method:'POST' }), onSuccess:() => queryClient.invalidateQueries({ queryKey:['my-projects'] }) })
  return <section className="workspace-page"><p className="eyebrow">PROJECT CONTROL</p><h1>我的项目</h1><p className="page-intro">从招募、协作执行到项目评价，所有节点都保留在同一个项目档案中。</p><div className="managed-project-list">{projects.data?.map((project) => <article className="manage-card" key={project.id}><div><span>{project.audit_status === 'pending' ? '等待管理员审核' : statusLabel(project.audit_status)}</span><h2>{project.title}</h2><p>{statusLabel(project.lifecycle_status)} · {project.positions?.length || 0} 个岗位</p></div><div className="manage-actions">{project.audit_status === 'approved' && project.lifecycle_status === 'recruiting' && <button onClick={() => move.mutate({ id:project.id, action:'start' })}>开始项目</button>}{project.lifecycle_status === 'in_progress' && <button onClick={() => move.mutate({ id:project.id, action:'finish-work' })}>结束执行</button>}<Link to={`/requester/projects/${project.id}/workspace`}>协作看板<ArrowUpRight size={16} /></Link><Link to={`/requester/projects/${project.id}/applicants`}><UsersRound size={16} />申请者</Link>{project.lifecycle_status === 'awaiting_review' && <Link to={`/requester/projects/${project.id}/review`}>去评价</Link>}</div></article>)}</div>{move.isError && <p className="form-error">{move.error.message}</p>}</section>
}
