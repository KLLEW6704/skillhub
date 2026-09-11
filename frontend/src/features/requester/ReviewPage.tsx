import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ClipboardCheck } from 'lucide-react'
import type { FormEvent } from 'react'
import { useParams } from 'react-router-dom'
import { apiRequest } from '../../lib/api'
import type { Application, RubricDefinition } from '../../lib/types'

export function ReviewPage() {
  const { id } = useParams()
  const queryClient = useQueryClient()
  const applicants = useQuery({ queryKey:['applicants', id], queryFn:() => apiRequest<Application[]>(`/api/v1/projects/${id}/applications`) })
  const rubrics = useQuery({ queryKey:['review-rubrics'], queryFn:() => apiRequest<RubricDefinition[]>('/api/v1/review-rubrics') })
  const submitReview = useMutation({ mutationFn:({ studentId, data }:{ studentId:number; data:unknown }) => apiRequest(`/api/v1/projects/${id}/reviews/${studentId}`, { method:'POST', body:JSON.stringify(data) }), onSuccess:() => { queryClient.invalidateQueries({ queryKey:['applicants', id] }) } })

  function submit(event:FormEvent<HTMLFormElement>, studentId:number, rubric:RubricDefinition) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    submitReview.mutate({ studentId, data:{ criteria_scores:Object.fromEntries(rubric.criteria.map((criterion) => [criterion, Number(data.get(criterion))])), comment:data.get('comment') } })
  }

  const pending = applicants.data?.filter((item) => item.status === 'accepted') ?? []
  return <section className="workspace-page classified-review-page"><p className="eyebrow">ROLE-BASED PROJECT REVIEW</p><h1>项目岗位评价</h1><p className="page-intro">项目结束后按实际岗位评价学生。代码、设计、数据、内容和运营岗位使用不同维度，评价会进入学生档案中的“真实项目记录”。</p>
    <div className="review-boundary"><ClipboardCheck size={21} /><p><b>项目表现评价与作品技能核验相互独立</b><span>这里记录真实协作与交付；作品证据仍需经过 AI 辅助初评和人工核验流程。</span></p></div>
    {pending.map((application) => {
      const category = application.position?.category || 'general'
      const rubric = rubrics.data?.find((item) => item.category === category) || rubrics.data?.find((item) => item.category === 'general')
      if (!rubric) return <div className="page-state" key={application.id}>正在读取岗位评价体系…</div>
      return <form className="classified-review-card" onSubmit={(event) => submit(event, application.student_id, rubric)} key={application.id}>
        <header><div><span>{rubric.label} · {rubric.version}</span><h2>{application.student?.display_name ?? `学生 ${application.student_id}`}</h2><p>{application.position?.title || '综合岗位'}</p></div><b>{rubric.scale_min}–{rubric.scale_max} 分</b></header>
        <div className="criteria-score-grid">{rubric.criteria.map((criterion, index) => <label key={criterion}><span><i>{String(index + 1).padStart(2, '0')}</i>{criterion}</span><select name={criterion} defaultValue="" required><option value="" disabled>请选择</option>{[1,2,3,4,5].map((score) => <option value={score} key={score}>{score} 分</option>)}</select></label>)}</div>
        <label className="review-comment">事实评价<textarea name="comment" placeholder="请记录具体任务、协作表现、交付结果和可改进之处" /></label>
        <footer><p>提交后不可重复评价，请确认内容准确。</p><button className="primary-button" disabled={submitReview.isPending}>{submitReview.isPending && submitReview.variables?.studentId === application.student_id ? '提交中…' : '确认并写入档案'}</button></footer>
      </form>
    })}
    {!applicants.isLoading && !pending.length && <div className="empty-state"><h2>没有待评价成员</h2><p>项目进入待评价阶段且存在已录用成员时，会在这里显示岗位评价表。</p></div>}
    {submitReview.isError && <p className="form-error" role="alert">{submitReview.error.message}</p>}
  </section>
}
