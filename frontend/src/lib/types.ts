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
