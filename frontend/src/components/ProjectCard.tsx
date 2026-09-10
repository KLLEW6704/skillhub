import { ArrowUpRight, CalendarDays } from 'lucide-react'
import { Link } from 'react-router-dom'
import { statusLabel } from '../lib/status'
import type { Project } from '../lib/types'

export function ProjectCard({ project, index = 1 }: { project: Project; index?: number }) {
  return <article className="project-card">
    <div className="project-card-main">
      <div className="project-card-top"><span>PROJECT / {String(index).padStart(2, '0')}</span><span>{project.category}</span></div>
      <h3><Link to={`/projects/${project.id}`}>{project.title}</Link></h3>
      <p>{project.description}</p>
      <div className="skill-tags">{project.required_skills.map((skill) => <span key={skill}>{skill}</span>)}</div>
      <div className="project-meta"><span><CalendarDays size={15} />{project.deadline}</span><strong>{project.budget ? `条件参考 ¥${project.budget}` : '志愿实践'}</strong><Link aria-label={`查看${project.title}`} to={`/projects/${project.id}`}><ArrowUpRight /></Link></div>
    </div>
    <aside className="project-card-aside" aria-label="项目招募概览">
      <div className="project-card-status"><small>当前状态</small><strong>{statusLabel(project.lifecycle_status)}</strong></div>
      <dl>
        <div><dt>申请截止</dt><dd>{project.deadline}</dd></div>
        <div><dt>项目条件</dt><dd>{project.budget ? `¥ ${project.budget}` : '志愿实践'}</dd></div>
      </dl>
      <div className="project-card-delivery"><small>交付内容</small><p>{project.deliverables || '进入详情查看交付要求'}</p></div>
      <Link className="project-card-link" aria-label={`查看${project.title}完整信息`} to={`/projects/${project.id}`}>查看完整项目 <ArrowUpRight size={18} /></Link>
    </aside>
  </article>
}
