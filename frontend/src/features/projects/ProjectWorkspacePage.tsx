import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, CalendarDays, CheckCircle2, Circle, Clock3, Plus, UsersRound } from 'lucide-react'
import type { FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { apiRequest } from '../../lib/api'
import { statusLabel } from '../../lib/status'
import type { ProjectTask, ProjectTaskStatus, ProjectWorkspace } from '../../lib/types'
import { useAuth } from '../auth/use-auth'

const columns:Array<{status:ProjectTaskStatus; title:string; icon:typeof Circle}> = [
  { status:'todo', title:'未完成', icon:Circle },
  { status:'in_progress', title:'处理中', icon:Clock3 },
  { status:'done', title:'已完成', icon:CheckCircle2 },
]

export function ProjectWorkspacePage() {
  const { id } = useParams()
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const workspace = useQuery({ queryKey:['project-workspace', id], queryFn:() => apiRequest<ProjectWorkspace>(`/api/v1/projects/${id}/workspace`) })
  const updateStatus = useMutation({
    mutationFn:({ task, status }:{task:ProjectTask; status:ProjectTaskStatus}) => apiRequest<ProjectTask>(`/api/v1/project-tasks/${task.id}/status`, { method:'PATCH', body:JSON.stringify({ status, expected_version:task.version }) }),
    onSuccess:() => queryClient.invalidateQueries({ queryKey:['project-workspace', id] }),
  })
  const addTask = useMutation({
    mutationFn:(payload:unknown) => apiRequest(`/api/v1/projects/${id}/tasks`, { method:'POST', body:JSON.stringify(payload) }),
    onSuccess:() => queryClient.invalidateQueries({ queryKey:['project-workspace', id] }),
  })

  function submitTask(event:FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const data = new FormData(form)
    addTask.mutate({ title:data.get('title'), description:data.get('description') || null, position_code:data.get('position_code') || null, assignee_student_id:data.get('assignee_student_id') ? Number(data.get('assignee_student_id')) : null, due_date:data.get('due_date') || null }, { onSuccess:() => form.reset() })
  }

  if (workspace.isLoading) return <div className="page-state">正在打开项目协作空间…</div>
  if (workspace.isError || !workspace.data) return <div className="page-state error">{workspace.error?.message || '无法打开项目协作空间'}</div>
  const data = workspace.data
  const basePath = user?.role === 'requester' ? '/requester/projects' : '/student/projects'
  const memberName = (id:number|null) => id ? data.members.find((member) => member.student_id === id)?.display_name || `学生 ${id}` : '待认领'
  const ownMembership = data.members.find((member) => member.student_id === user?.id)
  const canEditTask = (task:ProjectTask) => data.can_manage || task.assignee_student_id === user?.id || (task.assignee_student_id === null && task.position_id === ownMembership?.position_id)

  return <section className="workspace-page project-workspace-page">
    <Link className="back-link" to={basePath}><ArrowLeft size={16} />返回项目列表</Link>
    <header className="collaboration-hero">
      <div><p className="eyebrow">SHARED PROJECT WORKSPACE</p><h1>{data.project.title}</h1><p>项目方与学生看到的是同一组事项状态，任何更新都会同步到双方工作台。</p></div>
      <span className="lifecycle-stamp">{statusLabel(data.project.lifecycle_status)}</span>
    </header>

    <section className="progress-ledger" aria-label="项目总进度">
      <div><span>整体完成度</span><b>{data.progress.completion_percent}%</b></div>
      <div className="progress-track"><i style={{ width:`${data.progress.completion_percent}%` }} /></div>
      <dl><div><dt>全部事项</dt><dd>{data.progress.total}</dd></div><div><dt>未完成</dt><dd>{data.progress.todo}</dd></div><div><dt>处理中</dt><dd>{data.progress.in_progress}</dd></div><div><dt>已完成</dt><dd>{data.progress.done}</dd></div></dl>
    </section>

    <section className="project-roster"><div className="section-title-row"><div><p className="eyebrow">ROLE ROSTER</p><h2>岗位与成员</h2></div><span><UsersRound size={17} />{data.members.length} 位成员</span></div><div>{data.positions.map((position) => <article key={position.id}><span>{position.category}</span><h3>{position.title}</h3><p>{data.members.filter((member) => member.position_id === position.id).map((member) => member.display_name).join('、') || '尚未录用成员'}</p><small>{position.deliverables}</small></article>)}</div></section>

    {data.can_manage && ['recruiting', 'in_progress'].includes(data.project.lifecycle_status) && <form className="quick-task-form" onSubmit={submitTask}><div><p className="eyebrow">ADD TO THE CHAIN</p><h2>新增协作事项</h2></div><label>事项名称<input name="title" required /></label><label>岗位<select name="position_code"><option value="">全团队</option>{data.positions.map((position) => <option value={position.code} key={position.id}>{position.title}</option>)}</select></label><label>负责人<select name="assignee_student_id"><option value="">待认领</option>{data.members.map((member) => <option value={member.student_id} key={member.student_id}>{member.display_name} · {member.position_title || '未分岗'}</option>)}</select></label><label>截止日期<input name="due_date" type="date" /></label><label className="task-description-field">说明<input name="description" /></label><button className="primary-button" disabled={addTask.isPending}><Plus size={16} />{addTask.isPending ? '添加中…' : '加入任务链路'}</button>{addTask.isError && <p className="form-error" role="alert">{addTask.error.message}</p>}</form>}

    {data.project.lifecycle_status !== 'in_progress' && <p className="board-lock-note">项目进入“进行中”后，成员才可以改变事项状态。当前看板仍可用于查看活动链路。</p>}
    <section className="kanban-board" aria-label="项目事项看板">{columns.map(({ status, title, icon:Icon }) => <section className="kanban-column" key={status}><header><h2><Icon size={18} />{title}</h2><b>{data.tasks.filter((task) => task.status === status).length}</b></header><div>{data.tasks.filter((task) => task.status === status).map((task) => <article className="task-card" key={task.id}><div className="task-card-meta"><span>{task.position?.title || '全团队'}</span>{task.due_date && <small><CalendarDays size={13} />{task.due_date}</small>}</div><h3>{task.title}</h3>{task.description && <p>{task.description}</p>}<footer><span>{memberName(task.assignee_student_id)}</span><select aria-label={`更新 ${task.title} 的状态`} value={task.status} disabled={!canEditTask(task) || data.project.lifecycle_status !== 'in_progress' || (updateStatus.isPending && updateStatus.variables?.task.id === task.id)} onChange={(event) => updateStatus.mutate({ task, status:event.target.value as ProjectTaskStatus })}>{columns.map((column) => <option value={column.status} key={column.status}>{column.title}</option>)}</select></footer></article>)}</div>{!data.tasks.some((task) => task.status === status) && <p className="empty-column">暂无事项</p>}</section>)}</section>
    {updateStatus.isError && <p className="form-error board-error" role="alert">{updateStatus.error.message}</p>}
  </section>
}
