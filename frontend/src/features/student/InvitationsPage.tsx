import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowUpRight, BellRing, CalendarDays, MailOpen } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { apiRequest } from '../../lib/api'
import type { ProjectInvitation } from '../../lib/types'

const invitationLabels = {
  pending: '新邀约',
  viewed: '已查看',
  applied: '已申请',
} as const

export function InvitationsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const invitations = useQuery({ queryKey: ['my-invitations'], queryFn: () => apiRequest<ProjectInvitation[]>('/api/v1/invitations/mine') })
  const markViewed = useMutation({
    mutationFn: (id: number) => apiRequest<ProjectInvitation>(`/api/v1/invitations/${id}/view`, { method: 'POST' }),
    onSuccess: (updated) => queryClient.setQueryData<ProjectInvitation[]>(['my-invitations'], (old) => old?.map((item) => item.id === updated.id ? updated : item)),
  })

  const unread = invitations.data?.filter((item) => item.status === 'pending').length ?? 0
  async function openProject(invitation: ProjectInvitation) {
    try {
      if (invitation.status === 'pending') await markViewed.mutateAsync(invitation.id)
    } finally {
      navigate(`/projects/${invitation.project_id}`)
    }
  }

  return <section className="workspace-page invitations-workspace">
    <p className="eyebrow">PROJECT INVITATIONS</p>
    <h1>项目邀约</h1>
    <div className="invitation-summary">
      <span><BellRing size={21} /></span>
      <div><b>{unread ? `${unread} 条新邀约等待查看` : '所有邀约都已查看'}</b><p>邀约只是项目方的合作意向，你仍需查看项目并自主决定是否申请。</p></div>
    </div>
    {invitations.isLoading ? <div className="page-state">正在整理项目邀约…</div> : invitations.isError ? <div className="page-state error">邀约加载失败，请稍后重试</div> : invitations.data?.length ? <div className="invitation-list">{invitations.data.map((invitation) => <article className={`invitation-card ${invitation.status}`} key={invitation.id}>
      <header><span className="invitation-status"><MailOpen size={15} />{invitationLabels[invitation.status]}</span><time>{new Date(invitation.created_at).toLocaleDateString()}</time></header>
      <div className="invitation-card-body">
        <span className="evidence-kicker">{invitation.project.category}</span>
        <h2>{invitation.project.title}</h2>
        <p className="invitation-message">{invitation.message || '项目方认为你的技能档案与这个项目较为匹配，邀请你了解项目。'}</p>
        <div className="skill-tags">{invitation.project.required_skills.map((skill) => <span key={skill}>{skill}</span>)}</div>
      </div>
      <footer><span><CalendarDays size={15} />申请截止 {invitation.project.deadline}</span><button type="button" onClick={() => openProject(invitation)} disabled={markViewed.isPending && markViewed.variables === invitation.id}>查看项目详情 <ArrowUpRight size={17} /></button></footer>
    </article>)}</div> : <div className="empty-state invitation-empty"><b>∅</b><h2>暂时没有项目邀约</h2><p>完善技能与公开作品后，项目方可以从技能大厅向你发出合作邀请。</p></div>}
  </section>
}
