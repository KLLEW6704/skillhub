import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, expect, it } from 'vitest'
import { server } from '../../test/server'
import { ProjectFormPage } from './ProjectFormPage'

afterEach(cleanup)

it('applies the AI role and task draft without publishing the project', async () => {
  let planBody: Record<string, unknown> | undefined
  server.use(http.get('/api/v1/project-drafts', () => HttpResponse.json([])), http.post('/api/v1/projects/plan-draft', async ({ request }) => {
    planBody = await request.json() as Record<string, unknown>
    return HttpResponse.json({
      positions:[{ code:'developer', title:'后端开发', category:'development', description:'负责接口实现', headcount:1, required_skills:['Python'], deliverables:'接口与测试', sort_order:0 }],
      tasks:[{ title:'实现报名接口', description:'包含测试', position_code:'developer', assignee_student_id:null, due_date:null, sort_order:0 }],
    })
  }))
  const client = new QueryClient({ defaultOptions:{ queries:{ retry:false }, mutations:{ retry:false } } })
  render(<QueryClientProvider client={client}><MemoryRouter><ProjectFormPage /></MemoryRouter></QueryClientProvider>)
  fireEvent.change(screen.getByLabelText('项目名称'), { target:{ value:'校园技术节平台' } })
  fireEvent.change(screen.getByLabelText('项目分类'), { target:{ value:'技术实践' } })
  fireEvent.change(screen.getByLabelText('项目说明'), { target:{ value:'完成报名和活动数据服务' } })
  fireEvent.change(screen.getByLabelText('最终交付物'), { target:{ value:'可运行服务' } })
  fireEvent.click(screen.getByRole('button', { name:'AI 生成岗位与任务' }))
  expect(await screen.findByLabelText('岗位名称')).toHaveValue('后端开发')
  expect(screen.getByLabelText('任务名称')).toHaveValue('实现报名接口')
  expect(screen.getByText(/AI 只生成可编辑草案/)).toBeInTheDocument()
  expect(planBody).toMatchObject({ title:'校园技术节平台', category:'技术实践' })
})

it('saves an unfinished project as an account draft', async () => {
  let draftBody: Record<string, unknown> | undefined
  server.use(
    http.get('/api/v1/project-drafts', () => HttpResponse.json([])),
    http.post('/api/v1/project-drafts', async ({ request }) => {
      draftBody = await request.json() as Record<string, unknown>
      return HttpResponse.json({
        id:9,
        creator_id:2,
        payload:draftBody,
        created_at:'2026-09-11T08:00:00Z',
        updated_at:'2026-09-11T08:00:00Z',
      }, { status:201 })
    }),
  )
  const client = new QueryClient({ defaultOptions:{ queries:{ retry:false }, mutations:{ retry:false } } })
  render(<QueryClientProvider client={client}><MemoryRouter><ProjectFormPage /></MemoryRouter></QueryClientProvider>)
  fireEvent.change(screen.getByLabelText('项目名称'), { target:{ value:'尚未完成的迎新活动' } })
  fireEvent.click(screen.getByRole('button', { name:'保存草稿' }))
  expect(await screen.findByText('项目草稿已保存，可以稍后继续填写。')).toBeInTheDocument()
  expect(draftBody).toMatchObject({
    title:'尚未完成的迎新活动',
    description:'',
    deadline:'',
    positions:[],
    tasks:[],
  })
})
