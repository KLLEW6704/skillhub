import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { expect, it } from 'vitest'
import { server } from '../../test/server'
import { ReviewQueuePage } from './ReviewQueuePage'

it('gives a reviewer the evidence, dynamic defense, and adjustable rubric', async () => {
  server.use(http.get('/api/v1/reviewer/assignments', () => HttpResponse.json([{
    assignment_id: 2,
    verification: { id: 5, assessment_run_id: 8, student_id: 7, portfolio_id: 9, skill_id: 1, status: 'pending_human_review', human_result: null, credential: null, created_at: '2026-09-10', updated_at: '2026-09-10' },
    evidence: { id: 9, user_id: 7, skill_id: 1, title: '迎新海报', description: '作品说明', file_url: '/api/v1/portfolios/9/file', file_type: 'application/pdf', evidence_type: 'document', creation_context: '迎新活动', personal_role: '主设计', process_description: '草图到成稿', iteration_notes: '两轮修改', visibility: 'project_only', related_skill_ids: [1], ai_processing_consent_at: null, ai_supported: false, created_at: '2026-09-10' },
    defense: [{ question_id: 1, question: '如何证明是你的工作？', answer: '保留了源文件和迭代记录。' }],
    ai_result: { total_score: 78, result_label: 'AI 辅助初评、待人工复核', criteria: [{ criterion: '问题理解', score: 3, evidence: [{ source: 'defense_answer', reference: '答辩 1', reason: '说明了迭代过程' }] }] },
  }])))
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={client}><ReviewQueuePage /></QueryClientProvider>)
  expect(await screen.findByText('迎新海报')).toBeInTheDocument()
  expect(screen.getByText('如何证明是你的工作？')).toBeInTheDocument()
  expect(screen.getByDisplayValue('3')).toBeInTheDocument()
  expect(screen.getByLabelText('决定与调分理由')).toBeRequired()
})
