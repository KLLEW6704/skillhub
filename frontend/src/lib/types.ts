export type UserRole = 'student' | 'requester' | 'admin'

export interface User {
  id: number
  username: string
  email: string
  role: UserRole
  school: string | null
  college: string | null
  major: string | null
  grade: string | null
  is_active: boolean
}

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
}

export interface Project { id:number; creator_id:number; title:string; description:string; category:string; budget:string|null; deadline:string; audit_status:string; lifecycle_status:string; required_skills:string[]; created_at:string }
export interface ProjectPage { items:Project[]; total:number; page:number; page_size:number }
export interface Skill { id:number; user_id:number; name:string; description:string|null; growth_score:number; level:number; created_at:string }
export interface StudentProfile { user_id:number; username:string; display_name:string; avatar_url:string|null; bio:string|null; school:string|null; college:string|null; major:string|null; grade:string|null; skills:Skill[] }
export interface Review { id:number; project_id:number; student_id:number; skill_score:number; communication_score:number; delivery_score:number; time_management_score:number; comment:string|null; created_at:string }
export interface Portfolio { id:number;skill_id:number;title:string;description:string|null;file_url:string;file_type:string;created_at:string }
export interface Application { id:number;project_id:number;student_id:number;message:string|null;status:'pending'|'accepted'|'rejected'|'finished';created_at:string }
