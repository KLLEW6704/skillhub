import { createBrowserRouter } from 'react-router-dom'
import { AppShell } from '../components/AppShell'
import { LoginPage } from '../features/auth/LoginPage'
import { ProtectedRoute } from '../features/auth/ProtectedRoute'
import { RegisterPage } from '../features/auth/RegisterPage'

function Home() { return <section className="home-hero"><p className="eyebrow">SKILL GROWTH ARCHIVE · 2026</p><h1>把技能写进<br/><em>真实发生的事</em>里</h1><p className="hero-copy">连接校园项目、作品证据与同行评价。不是一句“我会”，而是一份可展示、可验证、持续成长的技能档案。</p><div className="hero-actions"><a className="primary-button" href="/projects">浏览实践项目</a><a className="secondary-button" href="/register">建立我的档案</a></div><div className="growth-strip">{['创建技能','提交作品','参与项目','获得评价'].map((item, index)=><div key={item}><b>0{index+1}</b><span>{item}</span></div>)}</div></section> }
function Placeholder({ title }: { title: string }) { return <section className="placeholder"><p className="eyebrow">ARCHIVE SECTION</p><h1>{title}</h1><p>该工作区将在后续任务中接入完整数据。</p></section> }

export const router = createBrowserRouter([{ element: <AppShell />, children: [
  { path: '/', element: <Home /> }, { path: '/login', element: <LoginPage /> }, { path: '/register', element: <RegisterPage /> },
  { path: '/projects', element: <Placeholder title="项目大厅" /> }, { path: '/talent', element: <Placeholder title="技能大厅" /> }, { path: '/403', element: <Placeholder title="无权访问这份档案" /> },
  { element: <ProtectedRoute allowedRoles={['student']} />, children: [{ path: '/student', element: <Placeholder title="学生工作台" /> }] },
  { element: <ProtectedRoute allowedRoles={['requester']} />, children: [{ path: '/requester', element: <Placeholder title="需求方工作台" /> }] },
  { element: <ProtectedRoute allowedRoles={['admin']} />, children: [{ path: '/admin', element: <Placeholder title="管理工作台" /> }] },
  { path: '*', element: <Placeholder title="档案页不存在" /> },
] }])
