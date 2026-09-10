import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { SkillLevel } from '../../components/SkillLevel'
import { apiRequest } from '../../lib/api'
import type { StudentProfile } from '../../lib/types'

export function TalentPage() {
  const { data, isLoading } = useQuery({ queryKey:['students'], queryFn:() => apiRequest<StudentProfile[]>('/api/v1/profiles/students') })
  return <section className="archive-page"><header className="page-heading"><div><p className="eyebrow">EVIDENCE-BASED TALENT ARCHIVE</p><h1>技能大厅</h1></div><p>成长活跃度反映参与和积累，不等于技能等级。进入个人档案后，可分别核对公开作品、人工核验与真实项目记录。</p></header>{isLoading ? <div className="page-state">整理学生档案…</div> : <div className="talent-grid">{data?.map((student,index) => <Link to={`/talent/${student.user_id}`} className="talent-card" key={student.user_id}><span className="talent-index">T-{String(index+1).padStart(3,'0')}</span><h2>{student.display_name}</h2><p>{student.school} · {student.major}</p><small>{student.portfolios.length} 份公开作品证据</small><div>{student.skills.slice(0,3).map((skill) => <SkillLevel skill={skill} key={skill.id} />)}</div></Link>)}</div>}</section>
}
