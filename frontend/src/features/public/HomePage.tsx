import { useQuery } from '@tanstack/react-query'
import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { ProjectCard } from '../../components/ProjectCard'
import { TalentCard } from '../../components/TalentCard'
import { apiRequest } from '../../lib/api'
import type { ProjectPage, StudentProfile } from '../../lib/types'

const projectFlow = [
  ['01', '发布真实需求', '明确目标、交付物与招募条件'],
  ['02', '招募或主动邀约', '从技能档案找到合适的学生'],
  ['03', '推进协作与交付', '让项目进展和实践结果持续留痕'],
  ['04', '验收并留下评价', '把真实表现沉淀回学生档案'],
]

const demoAccounts = [
  ['student', '学生端'],
  ['designer', '设计师学生端'],
  ['campus_org', '项目方'],
  ['reviewer', '审核员'],
  ['admin', '管理员'],
]

export function HomePage() {
  const projects = useQuery({ queryKey: ['home-projects'], queryFn: () => apiRequest<ProjectPage>('/api/v1/projects?page_size=3') })
  const students = useQuery({ queryKey: ['home-students'], queryFn: () => apiRequest<StudentProfile[]>('/api/v1/profiles/students') })
  const projectItems = projects.data?.items ?? []
  const studentItems = students.data?.slice(0, 4) ?? []

  return <>
    <section className="home-hero">
      <div className="home-hero-layout">
        <div className="home-hero-main">
          <p className="eyebrow">PROJECT DELIVERY × VERIFIED TALENT</p>
          <h1>让真实项目推进，<br /><em>让每次交付有据可查</em></h1>
          <p className="hero-copy">项目方可以发布需求、寻找合适学生、推进协作与交付，并在项目完成后留下岗位评价；学生则通过作品、答辩与真实项目，持续建立可核验的技能档案。</p>
          <div className="hero-actions">
            <Link className="primary-button" to="/requester/new">项目方发起项目 <ArrowRight size={17} /></Link>
            <Link className="secondary-button" to="/talent">寻找技能人才</Link>
            <Link className="hero-text-link" to="/projects">学生查看实践机会 →</Link>
          </div>
          <aside className="home-demo-access" aria-label="演示账号">
            <div className="home-demo-heading"><span>DEMO ACCESS</span><Link to="/login">进入登录页 →</Link></div>
            <p>队员可以直接使用以下账号查看不同角色的演示页面。</p>
            <div className="home-demo-password"><span>统一密码</span><strong>Student123!</strong></div>
            <div className="home-demo-accounts">{demoAccounts.map(([username, role]) => <div key={username}><code>{username}</code><span>{role}</span></div>)}</div>
          </aside>
        </div>
        <aside className="home-project-panel" aria-label="项目推进闭环">
          <p>FOR PROJECT OWNERS / 项目方</p>
          <h2>从一个需求，推进到一次完整交付</h2>
          <ol>
            {projectFlow.map(([index, title, description]) => <li key={index}>
              <b>{index}</b>
              <span><strong>{title}</strong><small>{description}</small></span>
            </li>)}
          </ol>
          <footer>作品证据、项目结果与评价相互关联，项目回看有链路，学生成长有依据。</footer>
        </aside>
      </div>
    </section>

    <section className="home-section home-project-section">
      <div className="section-title">
        <span>01</span><h2>正在招募</h2>
        <p>真实需求、明确交付，找到合适的人共同推进。</p>
        <Link to="/projects">查看全部 →</Link>
      </div>
      {projects.isLoading ? <div className="home-list-state">正在整理招募项目…</div> : projects.isError ? <div className="home-list-state error">项目加载失败，请稍后重试</div> : projectItems.length ? <div className="project-grid home-project-grid">{projectItems.map((project, index) => <ProjectCard project={project} index={index + 1} key={project.id} />)}</div> : <div className="home-list-state">目前没有正在招募的项目</div>}
    </section>

    <section className="home-section paper-dark home-talent-section">
      <div className="section-title">
        <span>02</span><h2>成长中的学生</h2>
        <p>用公开作品、技能活跃度与真实项目记录认识候选人。</p>
        <Link to="/talent">浏览技能大厅 →</Link>
      </div>
      {students.isLoading ? <div className="home-list-state">正在整理学生档案…</div> : students.isError ? <div className="home-list-state error">档案加载失败，请稍后重试</div> : studentItems.length ? <div className="talent-grid home-talent-grid">{studentItems.map((student, index) => <TalentCard student={student} index={index + 1} key={student.user_id} />)}</div> : <div className="home-list-state">还没有公开的学生档案</div>}
    </section>
  </>
}
