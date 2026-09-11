import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, expect, it } from 'vitest'
import { server } from '../../test/server'
import { PortfoliosPage } from './PortfoliosPage'

afterEach(cleanup)

it('shows saved evidence, privacy scope, and the real AI format boundary', async () => {
  const user = userEvent.setup()
  server.use(
    http.get('/api/v1/skills', () => HttpResponse.json([{ id: 1, user_id: 1, name: '视觉设计', description: null, growth_score: 0, level: 1, created_at: '2026-09-10' }])),
    http.get('/api/v1/portfolios', () => HttpResponse.json([{ id: 9, user_id: 1, skill_id: 1, title: '社团招新方案', description: '完整方案文档', file_url: '/api/v1/portfolios/9/file', file_type: 'application/pdf', evidence_type: 'document', creation_context: '社团招新', personal_role: '独立策划', process_description: '访谈后制作', iteration_notes: '根据反馈修改', visibility: 'private', related_skill_ids: [1], ai_processing_consent_at: null, ai_supported: false, created_at: '2026-09-10' }])),
    http.get('/api/v1/portfolios/drafts', () => HttpResponse.json([])),
    http.get('/api/v1/portfolios/9/assessments', () => HttpResponse.json([])),
  )
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={client}><MemoryRouter><PortfoliosPage /></MemoryRouter></QueryClientProvider>)
  expect(await screen.findByText('社团招新方案')).toBeInTheDocument()
  expect(screen.queryByText(/暂不支持 AI 评估/)).not.toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: '查看作品证据：社团招新方案' }))
  expect(await screen.findByText(/暂不支持 AI 评估/)).toBeInTheDocument()
  expect(screen.getByText(/不是学校官方认证/)).toBeInTheDocument()
})

it('saves an incomplete form as a durable draft without publishing evidence', async () => {
  const user = userEvent.setup()
  let savedDraft: Record<string, unknown> | null = null
  server.use(
    http.get('/api/v1/skills', () => HttpResponse.json([{ id: 1, user_id: 1, name: '视觉设计', description: null, growth_score: 0, level: 1, created_at: '2026-09-10' }])),
    http.get('/api/v1/portfolios', () => HttpResponse.json([])),
    http.get('/api/v1/portfolios/drafts', () => HttpResponse.json(savedDraft ? [savedDraft] : [])),
    http.post('/api/v1/portfolios/drafts', async ({ request }) => {
      const payload = await request.json() as Record<string, unknown>
      savedDraft = { id: 4, user_id: 1, ...payload, created_at: '2026-09-10T10:00:00Z', updated_at: '2026-09-10T10:00:00Z' }
      return HttpResponse.json(savedDraft, { status: 201 })
    }),
  )
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={client}><MemoryRouter><PortfoliosPage /></MemoryRouter></QueryClientProvider>)

  await user.click(await screen.findByRole('button', { name: '建立证据档案' }))
  expect(screen.getByRole('link', { name: '添加或管理技能' })).toHaveAttribute('href', '/student/skills')
  await user.type(screen.getByLabelText('作品标题'), '只填一半的作品')
  await user.type(screen.getByLabelText(/创作背景/), '课堂练习')
  await user.click(screen.getByRole('button', { name: '保存草稿' }))

  expect(await screen.findByText('只填一半的作品')).toBeInTheDocument()
  expect(savedDraft).toMatchObject({ title: '只填一半的作品', creation_context: '课堂练习', skill_id: null })
  expect(savedDraft).not.toHaveProperty('file')
})

it('opens a saved draft with its previous fields', async () => {
  const user = userEvent.setup()
  server.use(
    http.get('/api/v1/skills', () => HttpResponse.json([{ id: 1, user_id: 1, name: '视觉设计', description: null, growth_score: 0, level: 1, created_at: '2026-09-10' }])),
    http.get('/api/v1/portfolios', () => HttpResponse.json([])),
    http.get('/api/v1/portfolios/drafts', () => HttpResponse.json([{ id: 4, user_id: 1, skill_id: 1, title: '待继续的海报', description: null, evidence_type: 'visual_poster', creation_context: '迎新活动', personal_role: null, process_description: null, iteration_notes: null, visibility: 'private', related_skill_ids: [1], ai_processing_consent: false, created_at: '2026-09-10T10:00:00Z', updated_at: '2026-09-10T10:00:00Z' }])),
  )
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={client}><MemoryRouter><PortfoliosPage /></MemoryRouter></QueryClientProvider>)

  await user.click(await screen.findByRole('button', { name: '继续填写' }))

  expect(screen.getByLabelText('作品标题')).toHaveValue('待继续的海报')
  expect(screen.getByLabelText(/创作背景/)).toHaveValue('迎新活动')
  expect(screen.getByText(/草稿不会保留已选文件/)).toBeInTheDocument()
})
