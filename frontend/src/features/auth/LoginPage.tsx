import { ArrowRight, KeyRound } from 'lucide-react'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ApiError } from '../../lib/api'
import { useAuth } from './auth-store'

export function LoginPage() {
  const { login } = useAuth(); const navigate = useNavigate(); const location = useLocation()
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError('')
    const data = new FormData(event.currentTarget)
    try {
      const user = await login(String(data.get('username')), String(data.get('password')))
      const fallback = user.role === 'admin' ? '/admin' : user.role === 'requester' ? '/requester' : '/student'
      navigate((location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? fallback, { replace: true })
    } catch (reason) { setError(reason instanceof ApiError ? reason.message : '登录失败，请重试') } finally { setBusy(false) }
  }
  return <section className="auth-layout"><div className="auth-intro"><p className="eyebrow">ARCHIVE ACCESS / 01</p><h1>回到你的<br/><em>成长档案</em></h1><p>作品、项目与真实评价，共同记录技能如何一步步生长。</p><div className="archive-note"><span>演示账号</span><strong>student / Student123!</strong></div></div><form className="auth-card" onSubmit={submit}><div className="card-index">档案访问凭证</div><label>用户名<input name="username" required autoComplete="username" placeholder="输入用户名" /></label><label>密码<input name="password" type="password" required autoComplete="current-password" placeholder="输入密码" /></label>{error && <p className="form-error" role="alert">{error}</p>}<button className="primary-button" disabled={busy}><KeyRound size={17}/>{busy ? '核验中…' : '进入档案'}<ArrowRight size={17}/></button><p className="form-foot">还没有档案？<Link to="/register">现在建立</Link></p></form></section>
}
