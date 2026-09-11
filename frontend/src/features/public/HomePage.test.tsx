import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen, within } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, expect, it } from 'vitest'
import type { Project, StudentProfile } from '../../lib/types'
import { server } from '../../test/server'
import { HomePage } from './HomePage'

const project: Project = {
  id: 12, creator_id: 2, title: '校园公益短片招募', description: '为校园公益活动制作一支完整短片。', category: '校园实践', budget: '1000.00', deadline: '2026-10-01', audit_status: 'approved', lifecycle_status: 'recruiting', required_skills: ['视觉设计'], deliverables: '成片与项目文件', acceptance_criteria: '按期完成', created_at: '2026-09-01',
}

const student: StudentProfile = {
  user_id: 1, username: 'lin', display_name: '林同学', avatar_url: null, bio: null, school: '南方大学', college: '设计学院', major: '视觉传达', grade: '大二',
  skills: [{ id: 1, user_id: 1, name: '视觉设计', description: null, growth_score: 70, level: 3, created_at: '2026-09-10' }],
  portfolios: [{ id: 1, user_id: 1, skill_id: 1, title: '海报', description: '', file_url: '/poster.png', file_type: 'image/png', evidence_type: 'portfolio', creation_context: null, personal_role: null, process_description: null, iteration_notes: null, visibility: 'public', related_skill_ids: [], ai_processing_consent_at: null, ai_supported: false, created_at: '2026-09-10' }],
}

afterEach(cleanup)

function renderPage() {
  server.use(
    http.get('/api/v1/projects', () => HttpResponse.json({ items: [project], total: 1, page: 1, page_size: 3 })),
    http.get('/api/v1/profiles/students', () => HttpResponse.json([student])),
  )
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<MemoryRouter><QueryClientProvider client={client}><HomePage /></QueryClientProvider></MemoryRouter>)
}

it('presents a project delivery path and clear role entry points', () => {
  renderPage()

  expect(screen.getByRole('heading', { name: /让真实项目推进/ })).toBeInTheDocument()
  const workflow = screen.getByLabelText('项目推进闭环')
  expect(within(workflow).getByText('发布真实需求')).toBeInTheDocument()
  expect(within(workflow).getByText('验收并留下评价')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: /项目方发起项目/ })).toHaveAttribute('href', '/requester/new')
  expect(screen.getByRole('link', { name: '寻找技能人才' })).toHaveAttribute('href', '/talent')
})

it('renders compact recruiting projects and the same evidence-rich talent cards as the talent hall', async () => {
  renderPage()

  expect(await screen.findByRole('heading', { name: '校园公益短片招募' })).toBeInTheDocument()
  expect(screen.getByText('校园实践 · 招募中')).toBeInTheDocument()
  const talentCard = await screen.findByRole('link', { name: /林同学/ })
  expect(talentCard).toHaveClass('talent-card')
  expect(within(talentCard).getByText('南方大学 · 视觉传达')).toBeInTheDocument()
  expect(within(talentCard).getByText('1 份公开作品证据')).toBeInTheDocument()
  expect(within(talentCard).getByText('视觉设计')).toBeInTheDocument()
})
