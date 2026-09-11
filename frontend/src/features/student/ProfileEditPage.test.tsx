import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, expect, it } from 'vitest'
import { server } from '../../test/server'
import { ProfileEditPage } from './ProfileEditPage'

afterEach(cleanup)

it('edits expanded student details and updates the public preview', async () => {
  const user = userEvent.setup()
  let saved: Record<string, unknown> | null = null
  const profile = {
    user_id: 1,
    display_name: '林同学',
    avatar_url: null,
    bio: '关注数据产品与校园实践。',
    school: '南方大学',
    college: '计算机学院',
    major: '数据科学',
    grade: '大三',
  }
  server.use(
    http.get('/api/v1/profiles/me', () => HttpResponse.json(profile)),
    http.patch('/api/v1/profiles/me', async ({ request }) => {
      saved = await request.json() as Record<string, unknown>
      return HttpResponse.json({ ...profile, ...saved })
    }),
  )
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={client}><MemoryRouter><ProfileEditPage /></MemoryRouter></QueryClientProvider>)

  expect(await screen.findByDisplayValue('南方大学')).toBeInTheDocument()
  expect(screen.getByLabelText('学院')).toHaveValue('计算机学院')
  expect(screen.getByText('南方大学 · 计算机学院 · 数据科学 · 大三')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: '查看完整公开档案' })).toHaveAttribute('href', '/talent/1')

  await user.clear(screen.getByLabelText('学院'))
  await user.type(screen.getByLabelText('学院'), '人工智能学院')
  await user.click(screen.getByRole('button', { name: '保存个人资料' }))

  expect(await screen.findByRole('status')).toHaveTextContent('个人资料已保存')
  expect(saved).toMatchObject({ college: '人工智能学院', major: '数据科学', grade: '大三' })
  expect(screen.getByText('南方大学 · 人工智能学院 · 数据科学 · 大三')).toBeInTheDocument()
})
