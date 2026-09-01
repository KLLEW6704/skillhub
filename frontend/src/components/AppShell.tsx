import { Archive, LogOut, Menu, X } from 'lucide-react'
import { useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../features/auth/auth-store'

export function AppShell() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  return <div className="site-shell">
    <header className="site-header">
      <Link className="brand" to="/"><span className="brand-mark"><Archive size={19} /></span><span>SkillHub<small>技能成长档案馆</small></span></Link>
      <button className="menu-toggle" onClick={() => setOpen(!open)} aria-label="切换导航">{open ? <X /> : <Menu />}</button>
      <nav className={open ? 'nav open' : 'nav'} aria-label="主导航">
        <NavLink to="/projects">项目大厅</NavLink><NavLink to="/talent">技能大厅</NavLink>
        {user ? <><span className="nav-user">档案号 · {user.username}</span><button className="text-button" onClick={logout}><LogOut size={15}/>退出</button></> : <><NavLink to="/login">登录</NavLink><Link className="nav-cta" to="/register">建立档案</Link></>}
      </nav>
    </header>
    <main><Outlet /></main>
    <footer className="site-footer"><span>SKILLHUB · CAMPUS PRACTICE ARCHIVE</span><span>让每次实践都有据可查</span></footer>
  </div>
}
