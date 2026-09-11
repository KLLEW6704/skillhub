import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Archive, BriefcaseBusiness, Clock3, Plus, Save, Sparkles, Trash2 } from 'lucide-react'
import type { FormEvent } from 'react'
import { useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest } from '../../lib/api'
import type { PositionCategory, ProjectDraftPayload, ProjectPlanDraft, SavedProjectDraft } from '../../lib/types'

type PositionDraft = ProjectPlanDraft['positions'][number]
type TaskDraft = ProjectPlanDraft['tasks'][number]

const categories: Array<[PositionCategory, string]> = [
  ['design', '设计创意'], ['development', '软件开发'], ['data', '数据分析'],
  ['content', '内容传播'], ['operations', '活动运营'], ['general', '综合协作'],
]

const blankPosition = (index:number):PositionDraft => ({ code:`position-${index + 1}`, title:'', category:'general', description:'', headcount:1, required_skills:[], deliverables:'', sort_order:index })
const blankTask = (index:number):TaskDraft => ({ title:'', description:null, position_code:null, assignee_student_id:null, due_date:null, sort_order:index })
const nextPosition = (items:PositionDraft[]) => {
  let number = 1
  while (items.some((item) => item.code === `position-${number}`)) number += 1
  return blankPosition(number - 1)
}

export function ProjectFormPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const formRef = useRef<HTMLFormElement>(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('')
  const [deliverables, setDeliverables] = useState('')
  const [teamSize, setTeamSize] = useState(4)
  const [positions, setPositions] = useState<PositionDraft[]>([])
  const [tasks, setTasks] = useState<TaskDraft[]>([])
  const [planApplied, setPlanApplied] = useState(false)
  const [activeDraft, setActiveDraft] = useState<SavedProjectDraft | null>(null)

  const drafts = useQuery({ queryKey:['project-drafts'], queryFn:() => apiRequest<SavedProjectDraft[]>('/api/v1/project-drafts') })

  const plan = useMutation({
    mutationFn:() => apiRequest<ProjectPlanDraft>('/api/v1/projects/plan-draft', { method:'POST', body:JSON.stringify({ title, description, category, deliverables:deliverables || null, team_size:teamSize }) }),
    onSuccess:(draft) => { setPositions(draft.positions); setTasks(draft.tasks); setPlanApplied(true) },
  })
  const saveDraft = useMutation({
    mutationFn:({ id, payload }:{id?:number; payload:ProjectDraftPayload}) => apiRequest<SavedProjectDraft>(id ? `/api/v1/project-drafts/${id}` : '/api/v1/project-drafts', { method:id ? 'PATCH' : 'POST', body:JSON.stringify(payload) }),
    onSuccess:(saved) => { setActiveDraft(saved); queryClient.invalidateQueries({ queryKey:['project-drafts'] }) },
  })
  const removeDraft = useMutation({
    mutationFn:(id:number) => apiRequest<void>(`/api/v1/project-drafts/${id}`, { method:'DELETE' }),
    onSuccess:(_, id) => { if (activeDraft?.id === id) resetComposer(); queryClient.invalidateQueries({ queryKey:['project-drafts'] }) },
  })
  const create = useMutation({ mutationFn:(payload:unknown) => apiRequest('/api/v1/projects', { method:'POST', body:JSON.stringify(payload) }), onSuccess:() => { queryClient.invalidateQueries({ queryKey:['project-drafts'] }); navigate('/requester/projects') } })
  const aggregateSkills = useMemo(() => Array.from(new Set(positions.flatMap((position) => position.required_skills))), [positions])

  function updatePosition(index:number, patch:Partial<PositionDraft>) {
    setPositions((items) => items.map((item, current) => current === index ? { ...item, ...patch } : item)); setPlanApplied(false)
  }
  function updateTask(index:number, patch:Partial<TaskDraft>) {
    setTasks((items) => items.map((item, current) => current === index ? { ...item, ...patch } : item)); setPlanApplied(false)
  }
  function submit(event:FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = Object.fromEntries(new FormData(event.currentTarget))
    const manualSkills = String(data.required_skills || '').split(/[,，]/).map((value) => value.trim()).filter(Boolean)
    create.mutate({ draft_id:activeDraft?.id ?? null, title, description, category, deliverables, deadline:data.deadline, budget:data.budget ? Number(data.budget) : null, acceptance_criteria:data.acceptance_criteria, required_skills:aggregateSkills.length ? aggregateSkills : manualSkills, positions:positions.map((position, index) => ({ ...position, code:position.code.trim(), sort_order:index })), tasks:tasks.filter((task) => task.title.trim()).map((task, index) => ({ ...task, title:task.title.trim(), sort_order:index })) })
  }
  function draftPayload(form:HTMLFormElement):ProjectDraftPayload {
    const data = new FormData(form)
    return { title, description, category, deliverables, team_size:teamSize, deadline:String(data.get('deadline') || ''), budget:String(data.get('budget') || ''), additional_skills:String(data.get('required_skills') || ''), acceptance_criteria:String(data.get('acceptance_criteria') || ''), positions:positions.map((position, index) => ({ ...position, sort_order:index })), tasks:tasks.map((task, index) => ({ ...task, sort_order:index })) }
  }
  function continueDraft(draft:SavedProjectDraft) {
    setActiveDraft(draft); setTitle(draft.payload.title); setDescription(draft.payload.description); setCategory(draft.payload.category); setDeliverables(draft.payload.deliverables); setTeamSize(draft.payload.team_size); setPositions(draft.payload.positions); setTasks(draft.payload.tasks); setPlanApplied(false)
  }
  function resetComposer() {
    setActiveDraft(null); setTitle(''); setDescription(''); setCategory(''); setDeliverables(''); setTeamSize(4); setPositions([]); setTasks([]); setPlanApplied(false)
  }
  const canPlan = title.trim().length >= 2 && description.trim().length >= 5 && category.trim().length > 0

  return <section className="workspace-page collaboration-builder">
    <p className="eyebrow">AI PROJECT ARCHITECT</p><h1>发布协作项目</h1>
    <p className="page-intro">先写清项目目标，再让 AI 生成岗位和任务草案。所有内容都会留在发布页，确认后才提交管理员审核。</p>
    {!!drafts.data?.length && <section className="project-draft-shelf" aria-labelledby="project-drafts-title"><div className="draft-shelf-heading"><div><Archive size={19} /><span><b id="project-drafts-title">未完成的项目草稿</b><small>草稿保存在当前项目方账号中</small></span></div>{activeDraft && <button type="button" onClick={resetComposer}>新建空白项目</button>}</div><div>{drafts.data.map((draft) => <article className={activeDraft?.id === draft.id ? 'active' : ''} key={draft.id}><span><Clock3 size={15} />{new Date(draft.updated_at).toLocaleString('zh-CN')}</span><h2>{draft.payload.title || '未命名项目草稿'}</h2><p>{draft.payload.description || '尚未填写项目说明'}</p><footer><button type="button" onClick={() => continueDraft(draft)}>{activeDraft?.id === draft.id ? '正在编辑' : '继续填写'}</button><button type="button" aria-label={`删除草稿：${draft.payload.title || '未命名项目草稿'}`} disabled={removeDraft.isPending} onClick={() => confirm('确认删除这份项目草稿？') && removeDraft.mutate(draft.id)}><Trash2 size={15} /></button></footer></article>)}</div></section>}
    {activeDraft && <div className="active-project-draft"><Save size={16} /><span>正在编辑草稿：<b>{activeDraft.payload.title || '未命名项目草稿'}</b></span></div>}
    <form ref={formRef} key={activeDraft?.id ?? 'new'} className="project-builder-form" onSubmit={submit}>
      <section className="builder-panel project-brief-panel">
        <div className="panel-heading"><span>01</span><div><h2>项目简报</h2><p>这是 AI 拆岗和后续协作看板的依据。</p></div></div>
        <div className="builder-grid">
          <label>项目名称<input value={title} onChange={(event) => setTitle(event.target.value)} required /></label>
          <label>项目分类<input value={category} onChange={(event) => setCategory(event.target.value)} placeholder="例如：校园活动 / 技术实践" required /></label>
          <label className="wide-field">项目说明<textarea value={description} onChange={(event) => setDescription(event.target.value)} required /></label>
          <label className="wide-field">最终交付物<textarea value={deliverables} onChange={(event) => setDeliverables(event.target.value)} placeholder="例如：活动网站、数据看板和结项报告" required /></label>
          <label>预计团队人数<input value={teamSize} onChange={(event) => setTeamSize(Number(event.target.value))} type="number" min="1" max="30" /></label>
          <label>截止日期<input name="deadline" type="date" defaultValue={activeDraft?.payload.deadline || ''} required /></label>
          <label>预算参考<input name="budget" type="number" min="0" defaultValue={activeDraft?.payload.budget || ''} /></label>
          <label>补充技能（无岗位时使用）<input name="required_skills" defaultValue={activeDraft?.payload.additional_skills || ''} placeholder="Python，视觉设计" /></label>
          <label className="wide-field">验收标准<textarea name="acceptance_criteria" defaultValue={activeDraft?.payload.acceptance_criteria || ''} placeholder="说明哪些结果代表项目完成" required /></label>
        </div>
        <div className="ai-plan-callout"><div><Sparkles size={20} /><p><b>AI 只生成可编辑草案</b><small>不会自动发布、录用学生或修改项目状态。</small></p></div><button type="button" className="secondary-button" disabled={!canPlan || plan.isPending} onClick={() => plan.mutate()}>{plan.isPending ? '正在拆解…' : 'AI 生成岗位与任务'}</button></div>
        {planApplied && <p className="success-note">草案已放入下方，请检查岗位人数、职责和任务链路。</p>}
        {plan.isError && <p className="form-error" role="alert">{plan.error.message}</p>}
      </section>

      <section className="builder-panel">
        <div className="panel-heading"><span>02</span><div><h2>项目岗位</h2><p>不同岗位会使用不同的作品证据与项目评价量表。</p></div><button type="button" className="icon-text-button" onClick={() => setPositions((items) => [...items, nextPosition(items)])}><Plus size={16} />添加岗位</button></div>
        <div className="position-editor-list">{positions.map((position, index) => <article className="position-editor" key={`${position.code}-${index}`}>
          <header><span><BriefcaseBusiness size={18} />岗位 {String(index + 1).padStart(2, '0')}</span><button type="button" aria-label={`删除岗位 ${position.title || index + 1}`} onClick={() => setPositions((items) => items.filter((_, current) => current !== index))}><Trash2 size={16} /></button></header>
          <div className="builder-grid compact-grid">
            <label>岗位名称<input value={position.title} onChange={(event) => updatePosition(index, { title:event.target.value })} required /></label>
            <label>岗位代码（系统标识）<input value={position.code} pattern="[a-z0-9][a-z0-9_-]*" onChange={(event) => updatePosition(index, { code:event.target.value })} required /></label>
            <label>岗位类别<select value={position.category} onChange={(event) => updatePosition(index, { category:event.target.value as PositionCategory })}>{categories.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
            <label>招募人数<input type="number" min="1" max="20" value={position.headcount} onChange={(event) => updatePosition(index, { headcount:Number(event.target.value) })} /></label>
            <label className="wide-field">主要职责<textarea value={position.description} onChange={(event) => updatePosition(index, { description:event.target.value })} required /></label>
            <label>所需技能<input value={position.required_skills.join('，')} onChange={(event) => updatePosition(index, { required_skills:event.target.value.split(/[,，]/).map((value) => value.trim()).filter(Boolean) })} placeholder="Python，接口开发" required /></label>
            <label>岗位交付物<textarea value={position.deliverables} onChange={(event) => updatePosition(index, { deliverables:event.target.value })} required /></label>
          </div>
        </article>)}</div>
        {!positions.length && <div className="empty-builder">尚未拆分岗位。可使用 AI 生成，也可以手动添加。</div>}
      </section>

      <section className="builder-panel">
        <div className="panel-heading"><span>03</span><div><h2>活动任务链路</h2><p>发布后，项目方与已录用学生在同一个三态看板中同步进度。</p></div><button type="button" className="icon-text-button" onClick={() => setTasks((items) => [...items, blankTask(items.length)])}><Plus size={16} />添加任务</button></div>
        <div className="task-editor-list">{tasks.map((task, index) => <article className="task-editor" key={index}>
          <span className="task-index">{String(index + 1).padStart(2, '0')}</span>
          <label>任务名称<input value={task.title} onChange={(event) => updateTask(index, { title:event.target.value })} required /></label>
          <label>负责岗位<select value={task.position_code ?? ''} onChange={(event) => updateTask(index, { position_code:event.target.value || null })}><option value="">全团队</option>{positions.map((position) => <option value={position.code} key={position.code}>{position.title || position.code}</option>)}</select></label>
          <label>任务说明<input value={task.description ?? ''} onChange={(event) => updateTask(index, { description:event.target.value || null })} /></label>
          <button type="button" aria-label={`删除任务 ${task.title || index + 1}`} onClick={() => setTasks((items) => items.filter((_, current) => current !== index))}><Trash2 size={16} /></button>
        </article>)}</div>
        {!tasks.length && <div className="empty-builder">尚未建立任务链路。项目发布后也可以在协作看板继续添加。</div>}
      </section>

      <footer className="builder-submit"><div><b>{activeDraft ? '草稿已接续' : '提交前确认'}</b><p>未填完可以保存草稿；提交审核后，对应草稿会自动移除。</p></div><div className="builder-submit-actions"><button type="button" className="draft-button" disabled={saveDraft.isPending} onClick={() => formRef.current && saveDraft.mutate({ id:activeDraft?.id, payload:draftPayload(formRef.current) })}><Save size={16} />{saveDraft.isPending ? '保存中…' : activeDraft ? '更新草稿' : '保存草稿'}</button><button className="primary-button" disabled={create.isPending}>{create.isPending ? '提交中…' : '提交项目审核'}</button></div></footer>
      {saveDraft.isSuccess && <p className="draft-save-success">项目草稿已保存，可以稍后继续填写。</p>}
      {saveDraft.isError && <p className="form-error" role="alert">{saveDraft.error.message}</p>}
      {create.isError && <p className="form-error" role="alert">{create.error.message}</p>}
    </form>
  </section>
}
