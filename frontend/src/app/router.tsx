import { createBrowserRouter } from 'react-router-dom'
import { AppShell } from '../components/AppShell'
import { LoginPage } from '../features/auth/LoginPage'
import { ProtectedRoute } from '../features/auth/ProtectedRoute'
import { RegisterPage } from '../features/auth/RegisterPage'
import { HomePage } from '../features/public/HomePage'
import { ProjectDetailPage } from '../features/public/ProjectDetailPage'
import { ProjectsPage } from '../features/public/ProjectsPage'
import { ProfilePage } from '../features/public/ProfilePage'
import { TalentPage } from '../features/public/TalentPage'
import { StudentLayout } from '../features/student/StudentLayout';import { OverviewPage } from '../features/student/OverviewPage';import { ProfileEditPage } from '../features/student/ProfileEditPage';import { SkillsPage } from '../features/student/SkillsPage';import { PortfoliosPage } from '../features/student/PortfoliosPage';import { ApplicationsPage } from '../features/student/ApplicationsPage'

function Placeholder({ title }: { title: string }) { return <section className="placeholder"><p className="eyebrow">ARCHIVE SECTION</p><h1>{title}</h1><p>该工作区将在后续任务中接入完整数据。</p></section> }

export const router = createBrowserRouter([{ element: <AppShell />, children: [
  { path: '/', element: <HomePage /> }, { path: '/login', element: <LoginPage /> }, { path: '/register', element: <RegisterPage /> },
  { path: '/projects', element: <ProjectsPage /> }, { path: '/projects/:id', element: <ProjectDetailPage /> }, { path: '/talent', element: <TalentPage /> }, { path: '/talent/:id', element: <ProfilePage /> }, { path: '/403', element: <Placeholder title="无权访问这份档案" /> },
  { element: <ProtectedRoute allowedRoles={['student']} />, children: [{path:'/student',element:<StudentLayout/>,children:[{index:true,element:<OverviewPage/>},{path:'profile',element:<ProfileEditPage/>},{path:'skills',element:<SkillsPage/>},{path:'portfolios',element:<PortfoliosPage/>},{path:'applications',element:<ApplicationsPage/>}]}] },
  { element: <ProtectedRoute allowedRoles={['requester']} />, children: [{ path: '/requester', element: <Placeholder title="需求方工作台" /> }] },
  { element: <ProtectedRoute allowedRoles={['admin']} />, children: [{ path: '/admin', element: <Placeholder title="管理工作台" /> }] },
  { path: '*', element: <Placeholder title="档案页不存在" /> },
] }])
