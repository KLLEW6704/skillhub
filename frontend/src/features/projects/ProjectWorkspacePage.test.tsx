import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { expect, it } from 'vitest'
import { server } from '../../test/server'
import type { User } from '../../lib/types'
import { AuthContext } from '../auth/auth-context'
import { ProjectWorkspacePage } from './ProjectWorkspacePage'

const requester:User = { id:8, username:'requester', email:'r@example.com', role:'requester', school:null, college:null, major:null, grade:null, is_active:true }

it('shows one shared three-state board and sends optimistic task version', async () => {
  let updateBody:Record<string, unknown>|undefined
  const workspace = {
    project:{ id:1, title:'校园技术节平台', lifecycle_status:'in_progress' },
    positions:[{ id:2, project_id:1, code:'developer', title:'后端开发', category:'development', description:'接口', headcount:1, required_skills:['Python'], deliverables:'接口与测试', sort_order:0 }],
    members:[{ student_id:3, display_name:'小林', position_id:2, position_title:'后端开发' }],
    tasks:[
      { id:10, project_id:1, position_id:2, title:'整理需求', description:null, status:'todo', assignee_student_id:3, due_date:null, sort_order:0, version:1, updated_by_id:null, created_at:'2026-01-01', updated_at:'2026-01-01', position:null },
      { id:11, project_id:1, position_id:2, title:'开发接口', description:'完成报名接口', status:'in_progress', assignee_student_id:3, due_date:'2026-10-01', sort_order:1, version:4, updated_by_id:3, created_at:'2026-01-01', updated_at:'2026-01-01', position:{ id:2, project_id:1, code:'developer', title:'后端开发', category:'development', description:'接口', headcount:1, required_skills:['Python'], deliverables:'接口与测试', sort_order:0 } },
      { id:12, project_id:1, position_id:2, title:'交付测试', description:null, status:'done', assignee_student_id:3, due_date:null, sort_order:2, version:2, updated_by_id:3, created_at:'2026-01-01', updated_at:'2026-01-01', position:null },
    ],
    progress:{ total:3, todo:1, in_progress:1, done:1, completion_percent:33 }, can_manage:true,
  }
  server.use(
    http.get('/api/v1/projects/1/workspace', () => HttpResponse.json(workspace)),
    http.patch('/api/v1/project-tasks/11/status', async ({ request }) => { updateBody = await request.json() as Record<string, unknown>; return HttpResponse.json({ ...workspace.tasks[1], status:'done', version:5 }) }),
  )
  const client = new QueryClient({ defaultOptions:{ queries:{ retry:false }, mutations:{ retry:false } } })
  render(<QueryClientProvider client={client}><AuthContext.Provider value={{ user:requester, isLoading:false, login:async()=>requester, logout:()=>undefined }}><MemoryRouter initialEntries={['/requester/projects/1/workspace']}><Routes><Route path="/requester/projects/:id/workspace" element={<ProjectWorkspacePage />} /></Routes></MemoryRouter></AuthContext.Provider></QueryClientProvider>)
  expect(await screen.findByRole('heading', { name:'校园技术节平台' })).toBeInTheDocument()
  expect(screen.getByText('整体完成度')).toBeInTheDocument()
  expect(screen.getByRole('heading', { name:'未完成' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name:'处理中' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name:'已完成' })).toBeInTheDocument()
  fireEvent.change(screen.getByLabelText('更新 开发接口 的状态'), { target:{ value:'done' } })
  await waitFor(() => expect(updateBody).toEqual({ status:'done', expected_version:4 }))
})
