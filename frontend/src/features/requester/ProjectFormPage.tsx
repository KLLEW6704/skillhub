import { useMutation } from '@tanstack/react-query'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest } from '../../lib/api'

export function ProjectFormPage() {
  const navigate = useNavigate()
  const create = useMutation({ mutationFn:(payload:unknown) => apiRequest('/api/v1/projects', { method:'POST', body:JSON.stringify(payload) }), onSuccess:() => navigate('/requester/projects') })
  function submit(event:FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = Object.fromEntries(new FormData(event.currentTarget))
    create.mutate({
      ...data,
      budget:data.budget ? Number(data.budget) : null,
      required_skills:String(data.required_skills).split(/[,，]/).map((value) => value.trim()).filter(Boolean),
    })
  }
  return <section className="workspace-page"><p className="eyebrow">REAL PROJECT BRIEF</p><h1>发布项目</h1><p className="page-intro">把交付物和验收标准写清楚，项目完成后才能形成可核验的真实项目记录。</p><form className="stack-form project-form" onSubmit={submit}>
    <label>项目名称<input name="title" required /></label>
    <label>项目说明<textarea name="description" required /></label>
    <label>分类<input name="category" required /></label>
    <label>所需技能<input name="required_skills" placeholder="摄影，视频剪辑" required /></label>
    <label>交付物<textarea name="deliverables" placeholder="例如：精选照片 30 张、90 秒回顾短片" required /></label>
    <label>验收标准<textarea name="acceptance_criteria" placeholder="例如：画面清晰、授权完整、在截止日前交付" required /></label>
    <label>截止日期<input name="deadline" type="date" required /></label>
    <label>预算参考<input name="budget" type="number" min="0" /></label>
    <button className="primary-button" disabled={create.isPending}>{create.isPending ? '提交中…' : '提交审核'}</button>
    {create.isError && <p className="form-error">{create.error.message}</p>}
  </form></section>
}
