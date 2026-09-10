import type { Skill } from '../lib/types'
const names = ['','开始记录','持续积累','实践活跃','长期参与']
const next = [0,20,60,120]
export function SkillLevel({ skill }: { skill: Skill }) { const target = next[skill.level] ?? skill.growth_score; const progress = skill.level === 4 ? 100 : Math.min(100, skill.growth_score / target * 100); return <div className="skill-level"><div><span>活跃度 {skill.level} 级</span><strong>{skill.name}</strong><small>{names[skill.level]}</small></div><div className="progress"><i style={{width:`${progress}%`}}/></div><b>{skill.growth_score} 成长活跃度</b></div> }
