import { Link } from 'react-router-dom'
import type { Skill, StudentProfile } from '../lib/types'
import { SkillLevel } from './SkillLevel'

interface TalentCardProps {
  student: StudentProfile
  index: number
  skills?: Skill[]
}

export function TalentCard({ student, index, skills = student.skills.slice(0, 3) }: TalentCardProps) {
  const education = [student.school, student.major].filter(Boolean).join(' · ')

  return <Link to={`/talent/${student.user_id}`} className="talent-card">
    <span className="talent-index">T-{String(index).padStart(3, '0')}</span>
    <h2>{student.display_name}</h2>
    <p>{education || '个人资料持续完善中'}</p>
    <small className="talent-evidence-count">{student.portfolios.length} 份公开作品证据</small>
    <div className="talent-card-skills">
      {skills.length ? skills.map((item) => <SkillLevel skill={item} key={item.id} />) : <span className="talent-card-empty">技能档案正在建立中</span>}
    </div>
  </Link>
}
