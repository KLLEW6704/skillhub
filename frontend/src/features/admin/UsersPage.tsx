import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '../../lib/api'
import { roleLabels } from '../../lib/status'
import type { User, UserRole } from '../../lib/types'

export function UsersPage() {
  const queryClient = useQueryClient()
  const users = useQuery({ queryKey:['admin-users'], queryFn:() => apiRequest<User[]>('/api/v1/admin/users') })
  const toggle = useMutation({ mutationFn:(user:User) => apiRequest(`/api/v1/admin/users/${user.id}/status`, { method:'PATCH', body:JSON.stringify({ is_active:!user.is_active }) }), onSuccess:() => queryClient.invalidateQueries({ queryKey:['admin-users'] }) })
  const changeRole = useMutation({ mutationFn:({ user, role }:{ user:User; role:Exclude<UserRole,'admin'> }) => apiRequest(`/api/v1/admin/users/${user.id}/role`, { method:'PATCH', body:JSON.stringify({ role }) }), onSuccess:() => queryClient.invalidateQueries({ queryKey:['admin-users'] }) })
  return <section className="workspace-page"><h1>用户与评审权限</h1><p className="page-intro">评审角色只能由管理员授予。评审可以处理被分配的复核任务，但不能管理用户或项目。</p>{users.data?.map((user) => <article className="record-item admin-user-row" key={user.id}>
    <div><b>{user.username}</b><span>{roleLabels[user.role]} · {user.is_active ? '已启用' : '已停用'}</span></div>
    <div className="record-actions">{user.role !== 'admin' && <select aria-label={`设置 ${user.username} 的角色`} value={user.role} onChange={(event) => changeRole.mutate({ user, role:event.target.value as Exclude<UserRole,'admin'> })}><option value="student">学生</option><option value="requester">项目方</option><option value="reviewer">评审</option></select>}<button onClick={() => confirm(`确认${user.is_active ? '停用' : '启用'}该用户？`) && toggle.mutate(user)}>{user.is_active ? '停用' : '启用'}</button></div>
  </article>)}</section>
}
