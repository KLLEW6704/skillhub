import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { expect, it } from 'vitest'
import { server } from '../../test/server'
import { VerificationsPage } from './VerificationsPage'

it('requires a reason before an administrator can revoke a pilot credential', async () => {
  let submittedReason = ''
  server.use(
    http.get('/api/v1/admin/users', () => HttpResponse.json([])),
    http.get('/api/v1/admin/verifications', () => HttpResponse.json([{ id: 4, assessment_run_id: 8, student_id: 7, portfolio_id: 9, skill_id: 1, status: 'verified', human_result: {}, credential: { name: 'SkillHub 试行技能徽章', credential_number: 'SH-PILOT-2026-ABC', qr_url: '/qr', issued_at: '2026-09-10', status: 'active' }, created_at: '2026-09-10', updated_at: '2026-09-10' }])),
    http.post('/api/v1/admin/credentials/SH-PILOT-2026-ABC/revoke', async ({ request }) => {
      submittedReason = String((await request.json() as { reason:string }).reason)
      return HttpResponse.json({ status:'revoked' })
    }),
  )
  const client = new QueryClient({ defaultOptions: { queries: { retry:false } } })
  render(<QueryClientProvider client={client}><VerificationsPage /></QueryClientProvider>)
  const button = await screen.findByRole('button', { name:'撤销试行徽章' })
  expect(button).toBeDisabled()
  fireEvent.change(screen.getByLabelText('撤销 SH-PILOT-2026-ABC 的理由'), { target:{ value:'材料归属出现争议' } })
  fireEvent.click(button)
  await waitFor(() => expect(submittedReason).toBe('材料归属出现争议'))
})
