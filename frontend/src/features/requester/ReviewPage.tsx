import { useMutation, useQuery } from '@tanstack/react-query'
import type { FormEvent } from 'react'
import { useParams } from 'react-router-dom'
import { apiRequest } from '../../lib/api'
import type { Application } from '../../lib/types'

const dimensions = [
  ['skill_score', '技能表现'], ['communication_score', '沟通协作'], ['delivery_score', '成果交付'], ['time_management_score', '时间管理'],
] as const

export function ReviewPage() {
  const { id } = useParams()
  const applicants = useQuery({ queryKey:['applicants', id], queryFn:() => apiRequest<Application[]>(`/api/v1/projects/${id}/applications`) })
  const submitReview = useMutation({ mutationFn:({ studentId, data }:{ studentId:number; data:unknown }) => apiRequest(`/api/v1/projects/${id}/reviews/${studentId}`, { method:'POST', body:JSON.stringify(data) }) })
  function submit(event:FormEvent<HTMLFormElement>, studentId:number) {
    event.preventDefault()
    const data = Object.fromEntries(new FormData(event.currentTarget))
    submitReview.mutate({ studentId, data:{ ...data, ...Object.fromEntries(dimensions.map(([name]) => [name, Number(data[name])])) } })
  }
  return <section className="workspace-page"><h1>项目评价</h1><p className="page-intro">评价会形成独立的真实项目验证记录，并影响成长活跃度；它不会替代技能人工核验。</p>{applicants.data?.filter((item) => item.status === 'accepted').map((item) => <form className="stack-form review-form" onSubmit={(event) => submit(event, item.student_id)} key={item.id}>
    <h2>{item.student?.display_name ?? `学生 ${item.student_id}`}</h2>
    {dimensions.map(([name, label]) => <label key={name}>{label}<input name={name} type="number" min="1" max="5" required /></label>)}
    <label>文字评价<textarea name="comment" placeholder="记录具体表现与交付事实" /></label>
    <button className="primary-button" disabled={submitReview.isPending}>提交评价</button>
  </form>)}</section>
}
