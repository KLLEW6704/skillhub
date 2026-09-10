import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, expect, it } from 'vitest'
import type { ProjectInvitation } from '../../lib/types'
import { server } from '../../test/server'
import { InvitationsPage } from './InvitationsPage'

const invitation: ProjectInvitation = {
  id: 10,
  project_id: 3,
  student_id: 1,
  inviter_id: 8,
  message: '你的视觉档案很适合这次合作',
  status: 'pending',
  created_at: '2026-09-10',
  viewed_at: null,
  project: {
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
  },
}

afterEach(cleanup)

it('marks a new invitation viewed before opening its project', async () => {
  let viewed = false
  server.use(
    http.get('/api/v1/invitations/mine', () => HttpResponse.json([invitation])),
    http.post('/api/v1/invitations/10/view', () => {
      viewed = true
      return HttpResponse.json({ ...invitation, status: 'viewed', viewed_at: '2026-09-10T10:00:00Z' })
    }),
  )
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  render(<QueryClientProvider client={client}><MemoryRouter initialEntries={['/student/invitations']}><Routes><Route path="/student/invitations" element={<InvitationsPage />} /><Route path="/projects/:id" element={<div>项目详情目标</div>} /></Routes></MemoryRouter></QueryClientProvider>)

  expect(await screen.findByText('1 条新邀约等待查看')).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: /查看项目详情/ }))

  expect(await screen.findByText('项目详情目标')).toBeInTheDocument()
  expect(viewed).toBe(true)
})
