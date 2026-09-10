import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { BookOpenCheck, PencilLine, Plus, Save, Trash2, X } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { ApiError, apiRequest } from '../../lib/api'
import type { Skill } from '../../lib/types'

function errorMessage(error: unknown, fallback: string) {
  return error instanceof ApiError ? error.message : fallback
}

function SkillRecord({ skill, index }: { skill: Skill; index: number }) {
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [error, setError] = useState('')
  const update = useMutation({
    mutationFn: (body: { name: string; description: string }) => apiRequest<Skill>(`/api/v1/skills/${skill.id}`, { method: 'PATCH', body: JSON.stringify(body) }),
    onSuccess: (updated) => {
      queryClient.setQueryData<Skill[]>(['my-skills'], (old) => old?.map((item) => item.id === updated.id ? updated : item))
      setEditing(false)
      setError('')
    },
    onError: (reason) => setError(errorMessage(reason, '技能修改失败')),
  })
  const remove = useMutation({
    mutationFn: () => apiRequest<void>(`/api/v1/skills/${skill.id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.setQueryData<Skill[]>(['my-skills'], (old) => old?.filter((item) => item.id !== skill.id))
      setError('')
    },
    onError: (reason) => setError(errorMessage(reason, '技能删除失败')),
  })

  function submitEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    update.mutate({ name: String(data.get('name')), description: String(data.get('description')) })
  }

  function confirmDelete() {
    if (confirm(`确认删除“${skill.name}”？若已关联作品，系统会保留技能并阻止删除。`)) remove.mutate()
  }

  return <article className="skill-manager-card">
    <header>
      <div className="skill-record-index">SK-{String(index + 1).padStart(2, '0')}</div>
      <div className="skill-record-title"><h2>{skill.name}</h2><p>{skill.description || '尚未填写技能说明'}</p></div>
      <div className="skill-record-level"><span>Lv{skill.level}</span><b>{skill.growth_score}</b><small>成长活跃度</small></div>
    </header>
    <div className="skill-record-actions">
      <button className="skill-edit-button" onClick={() => { setEditing(!editing); setError('') }} aria-expanded={editing}><PencilLine size={16} />{editing ? '收起编辑' : '编辑技能'}</button>
      <button className="skill-delete-button" onClick={confirmDelete} disabled={remove.isPending}><Trash2 size={16} />{remove.isPending ? '删除中…' : '删除技能'}</button>
    </div>
    {editing && <form className="skill-edit-form" onSubmit={submitEdit}>
      <label>编辑技能名称<input name="name" defaultValue={skill.name} required maxLength={80} /></label>
      <label>编辑技能说明<textarea name="description" defaultValue={skill.description ?? ''} maxLength={2000} /></label>
      <div><button className="primary-button" disabled={update.isPending}><Save size={15} />{update.isPending ? '保存中…' : '保存修改'}</button><button type="button" className="secondary-button" onClick={() => setEditing(false)}><X size={15} />取消</button></div>
    </form>}
    {error && <p role="alert" className="form-error skill-record-error">{error}</p>}
  </article>
}

export function SkillsPage() {
  const queryClient = useQueryClient()
  const [error, setError] = useState('')
  const skills = useQuery({ queryKey: ['my-skills'], queryFn: () => apiRequest<Skill[]>('/api/v1/skills') })
  const add = useMutation({
    mutationFn: (body: { name: string; description: string }) => apiRequest<Skill>('/api/v1/skills', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: (skill) => {
      queryClient.setQueryData<Skill[]>(['my-skills'], (old) => [...(old || []), skill])
      setError('')
    },
    onError: (reason) => setError(errorMessage(reason, '添加失败')),
  })

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const data = new FormData(form)
    add.mutate({ name: String(data.get('name')), description: String(data.get('description')) }, { onSuccess: () => form.reset() })
  }

  return <section className="workspace-page skills-workspace">
    <p className="eyebrow">SKILL RECORDS</p>
    <h1>技能管理</h1>
    <p className="page-intro">建立并维护你的技能方向。成长活跃度由作品、真实项目与项目评价自动累计。</p>
    <section className="skill-create-card">
      <header><span><BookOpenCheck size={21} /></span><div><h2>添加技能</h2><p>先建立技能方向，再为它补充作品和项目证据。</p></div></header>
      <form onSubmit={submit}>
        <label>技能名称<input name="name" aria-label="技能名称" required maxLength={80} placeholder="例如：数据分析" /></label>
        <label>技能说明<textarea name="description" maxLength={2000} placeholder="说明你希望持续积累的能力方向" /></label>
        <button className="primary-button" disabled={add.isPending}><Plus size={16} />{add.isPending ? '添加中…' : '添加技能'}</button>
      </form>
      {error && <p role="alert" className="form-error skill-create-error">{error}</p>}
    </section>
    <div className="skill-list-heading"><div><span className="evidence-kicker">MY SKILLS</span><h2>已建立的技能</h2></div><span>{skills.data?.length || 0} 项</span></div>
    <div className="skill-manager-list">{skills.data?.map((skill, index) => <SkillRecord skill={skill} index={index} key={skill.id} />)}</div>
    {!skills.isLoading && !skills.data?.length && <div className="empty-inline">尚未添加技能，从上方建立第一项技能。</div>}
  </section>
}
