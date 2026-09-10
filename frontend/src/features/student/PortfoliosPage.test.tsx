import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { expect, it } from 'vitest'
import { server } from '../../test/server'
import { PortfoliosPage } from './PortfoliosPage'

it('shows saved evidence, privacy scope, and the real AI format boundary', async () => {
  server.use(
    http.get('/api/v1/skills', () => HttpResponse.json([{ id: 1, user_id: 1, name: '视觉设计', description: null, growth_score: 0, level: 1, created_at: '2026-09-10' }])),
    http.get('/api/v1/portfolios', () => HttpResponse.json([{ id: 9, user_id: 1, skill_id: 1, title: '社团招新方案', description: '完整方案文档', file_url: '/api/v1/portfolios/9/file', file_type: 'application/pdf', evidence_type: 'document', creation_context: '社团招新', personal_role: '独立策划', process_description: '访谈后制作', iteration_notes: '根据反馈修改', visibility: 'private', related_skill_ids: [1], ai_processing_consent_at: null, ai_supported: false, created_at: '2026-09-10' }])),
    http.get('/api/v1/portfolios/9/assessments', () => HttpResponse.json([])),
  )
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={client}><PortfoliosPage /></QueryClientProvider>)
  expect(await screen.findByText('社团招新方案')).toBeInTheDocument()
  expect(screen.getAllByText('仅自己可见')).toHaveLength(2)
  expect(screen.getByText(/暂不支持 AI 评估/)).toBeInTheDocument()
  expect(screen.getByText(/不是学校官方认证/)).toBeInTheDocument()
})
