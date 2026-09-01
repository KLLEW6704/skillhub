import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiRequest } from '../../lib/api'
import type { StudentProfile } from '../../lib/types'
import { SkillLevel } from '../../components/SkillLevel'
export function TalentPage(){const {data,isLoading}=useQuery({queryKey:['students'],queryFn:()=>apiRequest<StudentProfile[]>('/api/v1/profiles/students')});return <section className="archive-page"><header className="page-heading"><div><p className="eyebrow">TALENT ARCHIVE</p><h1>技能大厅</h1></div><p>浏览由作品、项目和评价共同证明的校园技能档案。</p></header>{isLoading?<div className="page-state">整理学生档案…</div>:<div className="talent-grid">{data?.map((student,index)=><Link to={`/talent/${student.user_id}`} className="talent-card" key={student.user_id}><span className="talent-index">T-{String(index+1).padStart(3,'0')}</span><h2>{student.display_name}</h2><p>{student.school} · {student.major}</p><div>{student.skills.slice(0,3).map(s=><SkillLevel skill={s} key={s.id}/>)}</div></Link>)}</div>}</section>}
