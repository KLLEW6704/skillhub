import { render, screen } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { expect, it } from 'vitest'
import { AuthProvider } from './auth-store'
import { useAuth } from './use-auth'
import { server } from '../../test/server'

function AuthProbe() {
  const { user, isLoading } = useAuth()
  if (isLoading) return <span>载入中</span>
  return <span>{user?.username ?? '访客'}</span>
}

it('restores the current user when a saved token exists', async () => {
  localStorage.setItem('skillhub_token', 'saved-token')
  server.use(
    http.get('/api/v1/auth/me', ({ request }) => {
      expect(request.headers.get('Authorization')).toBe('Bearer saved-token')
      return HttpResponse.json({
        id: 1,
        username: 'student',
        email: 'student@example.com',
        role: 'student',
        school: 'SkillHub 大学',
        college: '计算机学院',
        major: '数据科学',
        grade: '2025',
        is_active: true,
      })
    }),
  )

  render(
    <AuthProvider>
      <AuthProbe />
    </AuthProvider>,
  )

  expect(await screen.findByText('student')).toBeInTheDocument()
})

it('clears an invalid saved token', async () => {
  localStorage.setItem('skillhub_token', 'expired-token')
  server.use(
    http.get('/api/v1/auth/me', () =>
      HttpResponse.json({ detail: '登录凭证无效' }, { status: 401 }),
    ),
  )

  render(
    <AuthProvider>
      <AuthProbe />
    </AuthProvider>,
  )

  expect(await screen.findByText('访客')).toBeInTheDocument()
  expect(localStorage.getItem('skillhub_token')).toBeNull()
})
