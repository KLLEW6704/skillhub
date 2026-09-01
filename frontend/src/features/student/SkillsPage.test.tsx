import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { expect, it } from 'vitest'
import { server } from '../../test/server'
import { SkillsPage } from './SkillsPage'

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
