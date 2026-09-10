import { useQuery } from '@tanstack/react-query'
import { NavLink, Outlet } from 'react-router-dom'
import { apiRequest } from '../../lib/api'
import type { ProjectInvitation } from '../../lib/types'

const links = [
  ['/student', '成长概览'],
  ['/student/profile', '个人资料'],
  ['/student/skills', '技能管理'],
  ['/student/portfolios', '作品证据与 AI 答辩'],
  ['/student/invitations', '项目邀约'],
  ['/student/applications', '我的申请'],
] as const

export function StudentLayout() {
  const invitations = useQuery({ queryKey: ['my-invitations'], queryFn: () => apiRequest<ProjectInvitation[]>('/api/v1/invitations/mine') })
  const unread = invitations.data?.filter((item) => item.status === 'pending').length ?? 0

  return <div className="workspace">
    <aside>
      <p className="eyebrow">STUDENT ARCHIVE</p>
      <h2>我的工作台</h2>
      <nav aria-label="学生工作台">
        {links.map(([to, label]) => <NavLink end={to === '/student'} to={to} key={to}><span>{label}</span>{to === '/student/invitations' && unread > 0 && <b className="workspace-nav-badge" aria-label={`${unread} 条未读邀约`}>{unread}</b>}</NavLink>)}
      </nav>
    </aside>
    <div className="workspace-main"><Outlet /></div>
  </div>
}
