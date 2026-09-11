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

it('groups the public profile into three sections and opens a combined work review', async () => {
  server.use(
    http.get('/api/v1/profiles/students/1', () => HttpResponse.json({
      user_id: 1,
      username: 'designer',
      display_name: '设计同学',
      avatar_url: null,
      bio: '用真实项目持续完善作品集。',
      school: '南方大学',
      college: '设计学院',
      major: '视觉传达',
      grade: '大二',
      skills: [{ id: 2, user_id: 1, name: '视觉设计', description: null, growth_score: 72, level: 3, created_at: '2026-09-10' }],
      portfolios: [{
        id: 9, user_id: 1, skill_id: 2, title: '迎新视觉系统', description: '迎新活动视觉设计', file_url: '/api/v1/portfolios/9/file', file_type: 'image/png',
        evidence_type: 'visual_poster', creation_context: '校园迎新', personal_role: '主视觉设计', process_description: '完成草图与定稿', iteration_notes: '根据反馈调整信息层级',
        visibility: 'public', related_skill_ids: [2], ai_processing_consent_at: '2026-09-10', ai_supported: true, created_at: '2026-09-10',
      }],
    })),
    http.get('/api/v1/profiles/students/1/reviews', () => HttpResponse.json([{
      id: 5, project_id: 6, student_id: 1, position_id: 3, rubric_category: 'design', rubric_version: 'design-performance-v1',
      criteria_scores: { '需求与方案': 5, '设计执行': 4 }, project_title: '毕业季视觉设计', position_title: '视觉设计师',
      skill_score: 5, communication_score: 4, delivery_score: 5, time_management_score: 4, comment: '成果完整，沟通顺畅。', created_at: '2026-09-10',
    }])),
    http.get('/api/v1/profiles/students/1/project-validations', () => HttpResponse.json([{
      id: 8, project_id: 6, student_id: 1, requester_id: 8, project_title: '毕业季视觉设计', position_title: '视觉设计师', position_category: 'design', rubric_version: 'design-performance-v1',
      criteria_scores: { '需求与方案': 5, '设计执行': 4 }, deliverables: '完整视觉系统', acceptance_criteria: '按约定交付并通过验收', required_skills: ['视觉设计'], outcome: 'completed', created_at: '2026-09-10',
    }])),
    http.get('/api/v1/profiles/students/1/verified-credentials', () => HttpResponse.json([{
      name: 'SkillHub 试行技能徽章', credential_number: 'SH-DEMO-001', status: 'active', rubric_version: 'visual-poster-v1', issuer: 'reviewer', issued_at: '2026-09-10', revoked_at: null,
      evidence_summary: { portfolio_id: 9, title: '迎新视觉系统', evidence_type: 'visual_poster' },
      ai_result: { total_score: 80, review_status: 'pending_human_review', criteria: [{ criterion: '视觉一致性', score: 3, evidence: [] }] },
      verified_result: { total_score: 90, human_review_reason: '作品与答辩内容能够相互印证。', criteria: [{ criterion: '视觉一致性', score: 4, evidence: [] }] },
    }])),
    http.get('/api/v1/portfolios/9/file', () => new HttpResponse(new Uint8Array([137, 80, 78, 71]), { headers: { 'Content-Type': 'image/png' } })),
  )
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  render(<QueryClientProvider client={client}><AuthContext.Provider value={{ user: null, isLoading: false, login: async () => requester, logout: () => undefined }}><MemoryRouter initialEntries={['/talent/1']}><Routes><Route path="/talent/:id" element={<ProfilePage />} /></Routes></MemoryRouter></AuthContext.Provider></QueryClientProvider>)

  expect(await screen.findByRole('heading', { name: '成长活跃度' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: '公开作品集' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: '项目经历' })).toBeInTheDocument()
  expect(screen.getByText('成果完整，沟通顺畅。')).toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: '查看作品集：迎新视觉系统' }))

  expect(await screen.findByRole('heading', { name: 'AI 初评与人工核验' })).toBeInTheDocument()
  expect(screen.getByText('AI 初评 3 / 4')).toBeInTheDocument()
  expect(screen.getByText('人工确认 4 / 4')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: '放大查看作品：迎新视觉系统' })).toBeInTheDocument()
})
