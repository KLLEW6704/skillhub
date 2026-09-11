import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, expect, it } from 'vitest'
import { server } from '../../test/server'
import { AuthContext } from '../auth/auth-context'
import { StudentLayout } from './StudentLayout'

afterEach(cleanup)

it('gives the student a direct link to preview their public profile', async () => {
  server.use(http.get('/api/v1/invitations/mine', () => HttpResponse.json([])))
  const user = { id:23, username:'student', email:'student@example.com', role:'student' as const, school:null, college:null, major:null, grade:null, is_active:true }
  const client = new QueryClient({ defaultOptions:{ queries:{ retry:false } } })
  render(<QueryClientProvider client={client}><AuthContext.Provider value={{ user, isLoading:false, login:async()=>user, logout:()=>undefined }}><MemoryRouter><StudentLayout /></MemoryRouter></AuthContext.Provider></QueryClientProvider>)
  expect(await screen.findByRole('link', { name:/预览我的档案/ })).toHaveAttribute('href', '/talent/23')
})
