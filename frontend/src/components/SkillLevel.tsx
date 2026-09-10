import { ChevronDown } from 'lucide-react'
import type { Skill } from '../lib/types'

const levels = [
  { level: 1, name: '兴趣者', range: '0–19', threshold: 0, description: '开始建立技能与作品记录' },
  { level: 2, name: '作品证明', range: '20–59', threshold: 20, description: '持续积累可核查的作品证据' },
  { level: 3, name: '项目实践者', range: '60–119', threshold: 60, description: '通过真实项目持续验证能力' },
  { level: 4, name: '优秀贡献者', range: '120+', threshold: 120, description: '形成长期、稳定的实践与贡献记录' },
] as const

function currentLevel(level: number) {
  return levels[Math.max(1, Math.min(level, 4)) - 1]
}

export function SkillLevel({ skill, interactive = false }: { skill: Skill; interactive?: boolean }) {
  const current = currentLevel(skill.level)
  const next = levels.find((item) => item.level === current.level + 1)
  const levelProgress = (current.level - 1) / (levels.length - 1) * 100

  if (!interactive) return <div className="skill-level">
    <div><span>活跃度 {current.level} 级</span><strong>{skill.name}</strong><small>{current.name}</small></div>
    <div className="progress"><i style={{ width: `${levelProgress}%` }} /></div>
    <b>{skill.growth_score} 成长活跃度</b>
  </div>

  return <details className="growth-level-card">
    <summary>
      <div className="growth-card-top">
        <div><span className="growth-skill-name">{skill.name}</span><small>活跃度等级</small></div>
        <span className="growth-expand"><span className="show-closed">查看全部等级</span><span className="show-open">收起等级说明</span><ChevronDown size={17} /></span>
      </div>
      <div className="growth-current">
        <strong>Lv{current.level}</strong>
        <div><h3>{current.name}</h3><p>{skill.growth_score} 成长活跃度</p></div>
      </div>
      <div className="growth-track" role="progressbar" aria-label={`${skill.name} 当前为活跃度 ${current.level} 级`} aria-valuemin={1} aria-valuemax={4} aria-valuenow={current.level}>
        <i style={{ width: `${levelProgress}%` }} />
        {levels.map((item) => <span className={item.level <= current.level ? 'reached' : ''} key={item.level} style={{ left: `${(item.level - 1) / (levels.length - 1) * 100}%` }}><b>{item.level}</b></span>)}
      </div>
      <div className="growth-track-labels" aria-hidden="true">{levels.map((item) => <span key={item.level}>Lv{item.level}</span>)}</div>
      <p className="growth-next">{next ? `距离 Lv${next.level}「${next.name}」还需 ${Math.max(0, next.threshold - skill.growth_score)} 点活跃度` : '已到达当前最高活跃度等级'}</p>
    </summary>
    <div className="growth-level-details">
      <header><h4>完整等级路径</h4><p>等级反映作品与项目参与积累，不等同于技能能力认证。</p></header>
      <ol>{levels.map((item) => <li className={`${item.level < current.level ? 'completed' : ''} ${item.level === current.level ? 'current' : ''}`} key={item.level}>
        <span>Lv{item.level}</span><strong>{item.name}</strong><small>{item.range} 活跃度</small><p>{item.description}</p>
      </li>)}</ol>
    </div>
  </details>
}
