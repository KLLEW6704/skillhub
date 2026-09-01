import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { expect, it } from 'vitest'
import { server } from '../../test/server'
import { ProjectsPage } from './ProjectsPage'

it('sends keyword category and skill filters as query parameters', async () => {
  let capturedUrl = ''
  server.use(
    http.get('/api/v1/projects', ({ request }) => {
      capturedUrl = request.url
      return HttpResponse.json({ items: [], total: 0, page: 1, page_size: 20 })
    }),
  )
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter><ProjectsPage /></MemoryRouter>
    </QueryClientProvider>,
  )

  fireEvent.change(screen.getByLabelText('关键词'), { target: { value: '毕业季' } })
  fireEvent.change(screen.getByLabelText('项目分类'), { target: { value: '校园文化' } })
  fireEvent.change(screen.getByLabelText('所需技能'), { target: { value: '摄影' } })
  fireEvent.click(screen.getByRole('button', { name: '筛选项目' }))

  await screen.findByText('没有找到符合条件的项目')
  const params = new URL(capturedUrl).searchParams
  expect(params.get('keyword')).toBe('毕业季')
  expect(params.get('category')).toBe('校园文化')
  expect(params.get('skill')).toBe('摄影')
})
