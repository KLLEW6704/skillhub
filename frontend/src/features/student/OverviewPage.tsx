import { useQuery } from '@tanstack/react-query'
import { SkillLevel } from '../../components/SkillLevel'
import { apiRequest } from '../../lib/api'
import type { Application, Skill } from '../../lib/types'

export function OverviewPage() {
  const skills = useQuery({ queryKey: ['my-skills'], queryFn: () => apiRequest<Skill[]>('/api/v1/skills') })
  const applications = useQuery({ queryKey: ['my-apps'], queryFn: () => apiRequest<Application[]>('/api/v1/applications/mine') })

  return <section className="workspace-page">
    <p className="eyebrow">GROWTH OVERVIEW</p>
    <h1>成长概览</h1>
    <div className="stat-row">
      <div><b>{skills.data?.length || 0}</b><span>技能档案</span></div>
      <div><b>{applications.data?.length || 0}</b><span>项目申请</span></div>
      <div><b>{applications.data?.filter((item) => item.status === 'finished').length || 0}</b><span>完成项目</span></div>
    </div>
    {!!skills.data?.length && <section className="growth-overview-section">
      <header><div><span className="evidence-kicker">SKILL ACTIVITY PATH</span><h2>活跃度等级</h2></div><p>点击任一技能，查看完整等级与当前进度。</p></header>
      <div className="growth-level-list">{skills.data.map((skill) => <SkillLevel skill={skill} interactive key={skill.id} />)}</div>
    </section>}
  </section>
}
