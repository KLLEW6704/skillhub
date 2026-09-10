import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeAll, expect, it } from 'vitest'
import { AuthContext } from '../auth/auth-context'
import type { Project, User } from '../../lib/types'
import { server } from '../../test/server'
import { ProfilePage } from './ProfilePage'

const requester: User = {
  id: 8,
  username: 'requester',
  email: 'requester@example.com',
  role: 'requester',
  school: null,
  college: null,
  major: null,
  grade: null,
  is_active: true,
}

const project: Project = {
  id: 3,
  creator_id: 8,
  title: '校园公益短片',
  description: '制作公益短片',
  category: '校园实践',
  budget: '1000.00',
  deadline: '2099-10-01',
  audit_status: 'approved',
  lifecycle_status: 'recruiting',
  required_skills: ['视觉设计'],
  deliverables: '短片成品',
  acceptance_criteria: '按期交付',
  created_at: '2026-09-10',
}

beforeAll(() => {
  if (!HTMLDialogElement.prototype.showModal) {
    Object.defineProperty(HTMLDialogElement.prototype, 'showModal', { configurable: true, value(this: HTMLDialogElement) { this.setAttribute('open', '') } })
  }
  if (!HTMLDialogElement.prototype.close) {
    Object.defineProperty(HTMLDialogElement.prototype, 'close', { configurable: true, value(this: HTMLDialogElement) { this.removeAttribute('open') } })
  }
})

afterEach(cleanup)

it('lets a requester invite a student from the profile header', async () => {
  let invitationBody: { student_id: number; message: string } | undefined
  server.use(
    http.get('/api/v1/profiles/students/1', () => HttpResponse.json({
      user_id: 1,
      username: 'designer',
      display_name: '设计同学',
      avatar_url: null,
      bio: null,
      school: '南方大学',
      college: '设计学院',
      major: '视觉传达',
      grade: '大二',
      skills: [],
      portfolios: [],
    })),
    http.get('/api/v1/profiles/students/1/reviews', () => HttpResponse.json([])),
    http.get('/api/v1/profiles/students/1/project-validations', () => HttpResponse.json([])),
    http.get('/api/v1/profiles/students/1/verified-credentials', () => HttpResponse.json([])),
    http.get('/api/v1/projects/mine', () => HttpResponse.json([project])),
    http.post('/api/v1/projects/3/invitations', async ({ request }) => {
      invitationBody = await request.json() as { student_id: number; message: string }
      return HttpResponse.json({
        id: 10,
        project_id: 3,
        student_id: 1,
        inviter_id: 8,
        message: invitationBody.message,
        status: 'pending',
        created_at: '2026-09-10',
        viewed_at: null,
        project,
      }, { status: 201 })
    }),
  )
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  render(<QueryClientProvider client={client}><AuthContext.Provider value={{ user: requester, isLoading: false, login: async () => requester, logout: () => undefined }}><MemoryRouter initialEntries={['/talent/1']}><Routes><Route path="/talent/:id" element={<ProfilePage />} /></Routes></MemoryRouter></AuthContext.Provider></QueryClientProvider>)

  fireEvent.click(await screen.findByRole('button', { name: /邀约参与项目/ }))
  expect(await screen.findByRole('option', { name: '校园公益短片' })).toBeInTheDocument()
  fireEvent.change(screen.getByPlaceholderText('简单说明为什么希望邀请这位同学参与项目'), { target: { value: '你的作品很适合这次合作' } })
  fireEvent.click(screen.getByRole('button', { name: '发送项目邀约' }))

  expect(await screen.findByRole('heading', { name: '邀约已发送' })).toBeInTheDocument()
  expect(invitationBody).toEqual({ student_id: 1, message: '你的作品很适合这次合作' })
})
