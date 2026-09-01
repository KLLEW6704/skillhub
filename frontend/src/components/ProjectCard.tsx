import { ArrowUpRight, CalendarDays } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { Project } from '../lib/types'

export function ProjectCard({ project, index = 1 }: { project: Project; index?: number }) {
  return <article className="project-card"><div className="project-card-top"><span>PROJECT / {String(index).padStart(2,'0')}</span><span>{project.category}</span></div><h3><Link to={`/projects/${project.id}`}>{project.title}</Link></h3><p>{project.description}</p><div className="skill-tags">{project.required_skills.map(skill => <span key={skill}>{skill}</span>)}</div><div className="project-meta"><span><CalendarDays size={15}/>{project.deadline}</span><strong>{project.budget ? `条件参考 ¥${project.budget}` : '实践项目'}</strong><Link aria-label={`查看${project.title}`} to={`/projects/${project.id}`}><ArrowUpRight/></Link></div></article>
}
