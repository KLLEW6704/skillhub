import { createBrowserRouter } from 'react-router-dom'
import { AppShell } from '../components/AppShell'
import { AdminLayout } from '../features/admin/AdminLayout'
import { AssessmentRunsPage } from '../features/admin/AssessmentRunsPage'
import { OverviewPage as AdminOverview } from '../features/admin/OverviewPage'
import { ProjectsPage as AdminProjects } from '../features/admin/ProjectsPage'
import { UsersPage } from '../features/admin/UsersPage'
import { VerificationsPage } from '../features/admin/VerificationsPage'
import { LoginPage } from '../features/auth/LoginPage'
import { ProtectedRoute } from '../features/auth/ProtectedRoute'
import { RegisterPage } from '../features/auth/RegisterPage'
import { CredentialPage } from '../features/public/CredentialPage'
import { HomePage } from '../features/public/HomePage'
import { PlaceholderPage } from '../features/public/PlaceholderPage'
import { ProfilePage } from '../features/public/ProfilePage'
import { ProjectDetailPage } from '../features/public/ProjectDetailPage'
import { ProjectsPage } from '../features/public/ProjectsPage'
import { TalentPage } from '../features/public/TalentPage'
import { ApplicantsPage } from '../features/requester/ApplicantsPage'
import { MyProjectsPage } from '../features/requester/MyProjectsPage'
import { OverviewPage as RequesterOverview } from '../features/requester/OverviewPage'
import { ProjectFormPage } from '../features/requester/ProjectFormPage'
import { RequesterLayout } from '../features/requester/RequesterLayout'
import { ReviewPage } from '../features/requester/ReviewPage'
import { ReviewQueuePage } from '../features/reviewer/ReviewQueuePage'
import { ReviewerLayout } from '../features/reviewer/ReviewerLayout'
import { ProjectWorkspacePage } from '../features/projects/ProjectWorkspacePage'
import { ApplicationsPage } from '../features/student/ApplicationsPage'
import { InvitationsPage } from '../features/student/InvitationsPage'
import { OverviewPage } from '../features/student/OverviewPage'
import { PortfoliosPage } from '../features/student/PortfoliosPage'
import { ProfileEditPage } from '../features/student/ProfileEditPage'
import { SkillsPage } from '../features/student/SkillsPage'
import { StudentLayout } from '../features/student/StudentLayout'
import { ProjectWorkspacesPage } from '../features/student/ProjectWorkspacesPage'

export const router = createBrowserRouter([{ element:<AppShell />, children:[
  { path:'/', element:<HomePage /> }, { path:'/login', element:<LoginPage /> }, { path:'/register', element:<RegisterPage /> },
  { path:'/projects', element:<ProjectsPage /> }, { path:'/projects/:id', element:<ProjectDetailPage /> },
  { path:'/talent', element:<TalentPage /> }, { path:'/talent/:id', element:<ProfilePage /> },
  { path:'/credentials/:number', element:<CredentialPage /> }, { path:'/403', element:<PlaceholderPage title="无权访问这份档案" /> },
  { element:<ProtectedRoute allowedRoles={['student']} />, children:[{ path:'/student', element:<StudentLayout />, children:[{ index:true, element:<OverviewPage /> },{ path:'profile', element:<ProfileEditPage /> },{ path:'skills', element:<SkillsPage /> },{ path:'portfolios', element:<PortfoliosPage /> },{ path:'invitations', element:<InvitationsPage /> },{ path:'applications', element:<ApplicationsPage /> },{ path:'projects', element:<ProjectWorkspacesPage /> },{ path:'projects/:id', element:<ProjectWorkspacePage /> }] }] },
  { element:<ProtectedRoute allowedRoles={['requester']} />, children:[{ path:'/requester', element:<RequesterLayout />, children:[{ index:true, element:<RequesterOverview /> },{ path:'new', element:<ProjectFormPage /> },{ path:'projects', element:<MyProjectsPage /> },{ path:'projects/:id/workspace', element:<ProjectWorkspacePage /> },{ path:'projects/:id/applicants', element:<ApplicantsPage /> },{ path:'projects/:id/review', element:<ReviewPage /> }] }] },
  { element:<ProtectedRoute allowedRoles={['reviewer']} />, children:[{ path:'/reviewer', element:<ReviewerLayout />, children:[{ index:true, element:<ReviewQueuePage /> }] }] },
  { element:<ProtectedRoute allowedRoles={['admin']} />, children:[{ path:'/admin', element:<AdminLayout />, children:[{ index:true, element:<AdminOverview /> },{ path:'users', element:<UsersPage /> },{ path:'projects', element:<AdminProjects /> },{ path:'assessment-runs', element:<AssessmentRunsPage /> },{ path:'verifications', element:<VerificationsPage /> }] }] },
  { path:'*', element:<PlaceholderPage title="档案页不存在" /> },
] }])
