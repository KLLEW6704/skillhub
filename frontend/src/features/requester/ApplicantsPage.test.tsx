import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { expect, it } from 'vitest'
import { server } from '../../test/server'
import { ApplicantsPage } from './ApplicantsPage'

it('shows only the candidate work authorized for this project', async () => {
  server.use(http.get('/api/v1/projects/12/applications', () => HttpResponse.json([{
    id: 3, project_id: 12, student_id: 7, message: '我负责过校园活动视觉设计', status: 'pending', created_at: '2026-09-10',
    student: { user_id: 7, display_name: '林同学', skills: [{ id: 1, user_id: 7, name: '视觉设计', description: null, growth_score: 0, level: 1, created_at: '2026-09-10' }] },
    authorized_portfolios: [{ id: 9, user_id: 7, skill_id: 1, title: '迎新海报', description: '授权给本项目查看', file_url: '/api/v1/portfolios/9/file', file_type: 'application/pdf', evidence_type: 'document', creation_context: '', personal_role: '', process_description: '', iteration_notes: '', visibility: 'project_only', related_skill_ids: [1], ai_processing_consent_at: null, ai_supported: false, created_at: '2026-09-10', ai_assessment: null, verification_status: null, result_label: null }],
  }])))
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={client}><MemoryRouter initialEntries={['/requester/projects/12/applicants']}><Routes><Route path="/requester/projects/:id/applicants" element={<ApplicantsPage />} /></Routes></MemoryRouter></QueryClientProvider>)
  expect(await screen.findByText('林同学')).toBeInTheDocument()
  expect(screen.getByText('迎新海报')).toBeInTheDocument()
  expect(screen.getByText(/这里只展示学生主动授权/)).toBeInTheDocument()
  expect(screen.getByText('待处理')).toBeInTheDocument()
})
