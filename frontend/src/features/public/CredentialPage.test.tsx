import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { expect, it } from 'vitest'
import { server } from '../../test/server'
import { CredentialPage } from './CredentialPage'

it('presents a verifiable pilot credential without claiming school certification', async () => {
  server.use(http.get('/api/v1/credentials/SKILL-001', () => HttpResponse.json({ name: '视觉设计作品核验', credential_number: 'SKILL-001', status: 'active', rubric_version: 'visual-poster-v1', issuer: 'SkillHub 试行人工复核', issued_at: '2026-09-10T08:00:00Z', revoked_at: null, evidence_summary: { title: '迎新海报', evidence_type: 'visual_poster' }, verified_result: { total_score: 82, criteria: [{ criterion: '问题理解', score: 3, evidence: [] }] } })))
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={client}><MemoryRouter initialEntries={['/credentials/SKILL-001']}><Routes><Route path="/credentials/:number" element={<CredentialPage />} /></Routes></MemoryRouter></QueryClientProvider>)
  expect(await screen.findByText('视觉设计作品核验')).toBeInTheDocument()
  expect(screen.getByText('记录有效')).toBeInTheDocument()
  expect(screen.getByText(/不属于学历、文凭或学校官方认证/)).toBeInTheDocument()
})
