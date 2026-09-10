import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { afterEach, expect, it, vi } from 'vitest'
import { server } from '../../test/server'
import { SkillsPage } from './SkillsPage'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

it('creates a skill and displays a duplicate-name server error', async () => {
  let posts = 0
  server.use(
    http.get('/api/v1/skills', () => HttpResponse.json([])),
    http.post('/api/v1/skills', async () => {
      posts += 1
      if (posts > 1) return HttpResponse.json({ detail: '技能名称已存在' }, { status: 409 })
      return HttpResponse.json({ id: 1, user_id: 1, name: 'Python', description: '数据处理', growth_score: 0, level: 1, created_at: new Date().toISOString() }, { status: 201 })
    }),
  )
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={client}><SkillsPage /></QueryClientProvider>)
  const input = await screen.findByLabelText('技能名称')
  fireEvent.change(input, { target: { value: 'Python' } })
  fireEvent.click(screen.getByRole('button', { name: '添加技能' }))
  expect(await screen.findByText('Python')).toBeInTheDocument()
  fireEvent.change(input, { target: { value: 'Python' } })
  fireEvent.click(screen.getByRole('button', { name: '添加技能' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('技能名称已存在')
})

it('edits an existing skill and removes an unlinked skill', async () => {
  const skill = { id: 1, user_id: 1, name: 'Python', description: '数据处理', growth_score: 20, level: 2, created_at: '2026-09-10' }
  server.use(
    http.get('/api/v1/skills', () => HttpResponse.json([skill])),
    http.patch('/api/v1/skills/1', async ({ request }) => {
      const body = await request.json() as { name: string; description: string }
      return HttpResponse.json({ ...skill, ...body })
    }),
    http.delete('/api/v1/skills/1', () => new HttpResponse(null, { status: 204 })),
  )
  const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={client}><SkillsPage /></QueryClientProvider>)

  fireEvent.click(await screen.findByRole('button', { name: '编辑技能' }))
  fireEvent.change(screen.getByLabelText('编辑技能名称'), { target: { value: 'Python 自动化' } })
  fireEvent.click(screen.getByRole('button', { name: '保存修改' }))
  expect(await screen.findByRole('heading', { name: 'Python 自动化' })).toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: '删除技能' }))
  await waitFor(() => expect(screen.queryByRole('heading', { name: 'Python 自动化' })).not.toBeInTheDocument())
  expect(confirm).toHaveBeenCalledOnce()
  confirm.mockRestore()
})

it('shows why a skill linked to evidence cannot be deleted', async () => {
  const skill = { id: 1, user_id: 1, name: '视觉设计', description: null, growth_score: 10, level: 1, created_at: '2026-09-10' }
  server.use(
    http.get('/api/v1/skills', () => HttpResponse.json([skill])),
    http.delete('/api/v1/skills/1', () => HttpResponse.json({ detail: '技能仍有关联作品，不能删除' }, { status: 409 })),
  )
  const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={client}><SkillsPage /></QueryClientProvider>)

  fireEvent.click(await screen.findByRole('button', { name: '删除技能' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('技能仍有关联作品，不能删除')
  expect(screen.getByRole('heading', { name: '视觉设计' })).toBeInTheDocument()
  confirm.mockRestore()
})
