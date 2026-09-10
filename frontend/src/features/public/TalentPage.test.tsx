import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, expect, it } from 'vitest'
import type { StudentProfile } from '../../lib/types'
import { server } from '../../test/server'
import { TalentPage } from './TalentPage'

const students: StudentProfile[] = [
  {
    user_id: 1, username: 'lin', display_name: '林同学', avatar_url: null, bio: null, school: '南方大学', college: '设计学院', major: '视觉传达', grade: '大二',
    skills: [{ id: 1, user_id: 1, name: '视觉设计', description: null, growth_score: 70, level: 3, created_at: '2026-09-10' }],
    portfolios: [{
      id: 1, user_id: 1, skill_id: 1, title: '海报', description: '', file_url: '/poster.png', file_type: 'image/png',
      evidence_type: 'portfolio', creation_context: null, personal_role: null, process_description: null, iteration_notes: null,
      visibility: 'public', related_skill_ids: [], ai_processing_consent_at: null, ai_supported: false, created_at: '2026-09-10',
    }],
  },
  {
    user_id: 2, username: 'chen', display_name: '陈同学', avatar_url: null, bio: null, school: '科技学院', college: '计算机学院', major: '数据科学', grade: '大三',
    skills: [{ id: 2, user_id: 2, name: 'Python', description: null, growth_score: 130, level: 4, created_at: '2026-09-10' }],
    portfolios: [],
  },
]

afterEach(cleanup)

function renderPage() {
  server.use(http.get('/api/v1/profiles/students', () => HttpResponse.json(students)))
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<MemoryRouter><QueryClientProvider client={client}><TalentPage /></QueryClientProvider></MemoryRouter>)
}

it('filters talent profiles by keyword, skill and minimum activity level', async () => {
  renderPage()
  expect(await screen.findByRole('heading', { name: '林同学' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: '陈同学' })).toBeInTheDocument()

  fireEvent.change(screen.getByPlaceholderText('姓名、学校、专业或技能'), { target: { value: '数据科学' } })
  expect(screen.queryByRole('heading', { name: '林同学' })).not.toBeInTheDocument()
  expect(screen.getByRole('heading', { name: '陈同学' })).toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: '清除筛选' }))
  fireEvent.change(screen.getByLabelText('技能方向'), { target: { value: '视觉设计' } })
  fireEvent.change(screen.getByLabelText('最低活跃度'), { target: { value: '4' } })
  expect(screen.getByRole('heading', { name: '没有找到符合条件的档案' })).toBeInTheDocument()
})

it('sorts profiles by growth score and clears active filters', async () => {
  renderPage()
  expect(await screen.findByRole('link', { name: /林同学/ })).toBeInTheDocument()

  fireEvent.change(screen.getByLabelText('结果排序'), { target: { value: 'growth' } })
  const cards = screen.getAllByRole('link').filter((link) => link.classList.contains('talent-card'))
  expect(within(cards[0]).getByRole('heading', { name: '陈同学' })).toBeInTheDocument()
  expect(screen.getByText('筛选条件已生效')).toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: '清除筛选' }))
  expect((screen.getByLabelText('结果排序') as HTMLSelectElement).value).toBe('default')
})
