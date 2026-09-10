import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, expect, it } from 'vitest'
import type { Project } from '../lib/types'
import { ProjectCard } from './ProjectCard'

afterEach(cleanup)

it('uses project information instead of an image placeholder', () => {
  const project: Project = {
    id: 1,
    creator_id: 2,
    title: '校园公益短片招募',
    description: '为校园公益活动制作短片。',
    category: '校园实践',
    budget: '1000.00',
    deadline: '2026-10-01',
    audit_status: 'approved',
    lifecycle_status: 'recruiting',
    required_skills: ['视觉设计'],
    deliverables: '成片与项目文件',
    acceptance_criteria: '按期完成',
    created_at: '2026-09-01',
  }

  render(<MemoryRouter><ProjectCard project={project} /></MemoryRouter>)

  const overview = screen.getByLabelText('项目招募概览')
  expect(overview).toHaveTextContent('招募中')
  expect(overview).toHaveTextContent('成片与项目文件')
  expect(screen.queryByRole('img')).not.toBeInTheDocument()
  expect(screen.getByRole('link', { name: '查看校园公益短片招募完整信息' })).toHaveAttribute('href', '/projects/1')
})
