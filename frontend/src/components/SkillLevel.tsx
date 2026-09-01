import type { Skill } from '../lib/types'
const names = ['','兴趣者','作品证明','项目实践者','优秀贡献者']
const next = [0,20,60,120]
export function SkillLevel({ skill }: { skill: Skill }) { const target = next[skill.level] ?? skill.growth_score; const progress = skill.level === 4 ? 100 : Math.min(100, skill.growth_score / target * 100); return <div className="skill-level"><div><span>LV{skill.level}</span><strong>{skill.name}</strong><small>{names[skill.level]}</small></div><div className="progress"><i style={{width:`${progress}%`}}/></div><b>{skill.growth_score} PTS</b></div> }
