import { useQuery } from '@tanstack/react-query'
import { ArrowUpRight, Eye } from 'lucide-react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { apiRequest } from '../../lib/api'
import type { ProjectInvitation } from '../../lib/types'
import { useAuth } from '../auth/use-auth'

const links = [
  ['/student', '成长概览'],
  ['/student/profile', '个人资料'],
  ['/student/skills', '技能管理'],
  ['/student/portfolios', '作品证据与 AI 答辩'],
  ['/student/invitations', '项目邀约'],
  ['/student/applications', '我的申请'],
  ['/student/projects', '项目协作'],
] as const

export function StudentLayout() {
  const { user } = useAuth()
  const invitations = useQuery({ queryKey: ['my-invitations'], queryFn: () => apiRequest<ProjectInvitation[]>('/api/v1/invitations/mine') })
  const unread = invitations.data?.filter((item) => item.status === 'pending').length ?? 0

  return <div className="workspace">
    <aside>
      <p className="eyebrow">STUDENT ARCHIVE</p>
      <h2>我的工作台</h2>
      {user && <Link className="student-profile-preview-link" to={`/talent/${user.id}`}><Eye size={18} /><span><b>预览我的档案</b><small>查看项目方看到的公开内容</small></span><ArrowUpRight size={16} /></Link>}
      <nav aria-label="学生工作台">
        {links.map(([to, label]) => <NavLink end={to === '/student'} to={to} key={to}><span>{label}</span>{to === '/student/invitations' && unread > 0 && <b className="workspace-nav-badge" aria-label={`${unread} 条未读邀约`}>{unread}</b>}</NavLink>)}
      </nav>
    </aside>
    <div className="workspace-main"><Outlet /></div>
  </div>
}
