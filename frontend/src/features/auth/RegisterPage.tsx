import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { apiRequest, ApiError } from '../../lib/api'

export function RegisterPage() {
  const navigate = useNavigate(); const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(''); const data = Object.fromEntries(new FormData(event.currentTarget))
    try { await apiRequest('/api/v1/auth/register', { method: 'POST', body: JSON.stringify(data) }); navigate('/login', { replace: true }) }
    catch (reason) { setError(reason instanceof ApiError ? reason.message : '注册失败，请重试') } finally { setBusy(false) }
  }
  return <section className="auth-layout register"><div className="auth-intro"><p className="eyebrow">NEW ARCHIVE / 02</p><h1>从一次实践<br/>开始被<em>看见</em></h1><p>选择你的身份，建立一份持续生长、可以验证的校园技能档案。</p></div><form className="auth-card" onSubmit={submit}><div className="card-index">建立新档案</div><div className="field-row"><label>用户名<input name="username" required minLength={3}/></label><label>邮箱<input name="email" type="email" required/></label></div><label>密码<input name="password" type="password" required minLength={8}/></label><label>身份<select name="role" defaultValue="student"><option value="student">学生 · 展示技能</option><option value="requester">需求方 · 发布项目</option></select></label><label>学校 / 组织归属<input name="school" placeholder="可稍后完善"/></label>{error && <p className="form-error" role="alert">{error}</p>}<button className="primary-button" disabled={busy}>{busy ? '建档中…' : '确认建立档案'}</button><p className="form-foot">已有档案？<Link to="/login">直接登录</Link></p></form></section>
}
