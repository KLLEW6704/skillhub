import { fireEvent, render, screen } from '@testing-library/react'
import { expect, it } from 'vitest'
import { SkillLevel } from './SkillLevel'

it('shows the current growth level and expands the complete level path', () => {
  render(<SkillLevel interactive skill={{ id: 1, user_id: 1, name: '视觉设计', description: null, growth_score: 42, level: 2, created_at: '2026-09-10' }} />)

  expect(screen.getByRole('heading', { level: 3, name: '作品证明' })).toBeInTheDocument()
  expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '2')
  const summary = screen.getByText('查看全部等级').closest('summary')
  fireEvent.click(summary!)
  expect(summary?.closest('details')).toHaveAttribute('open')
  expect(screen.getByText('项目实践者')).toBeInTheDocument()
  expect(screen.getByText(/还需 18 点活跃度/)).toBeInTheDocument()
})
