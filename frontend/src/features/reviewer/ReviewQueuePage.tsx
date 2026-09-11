import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { FormEvent } from 'react'
import { SecureImage } from '../../components/SecureImage'
import { apiBlob, apiRequest } from '../../lib/api'
import { verificationLabels } from '../../lib/status'
import type { ReviewerAssignment } from '../../lib/types'

const outcomes = [['verified','通过并核验'],['more_evidence','要求补充材料'],['rejected','未通过']] as const

async function openEvidence(path:string) {
  const blob = await apiBlob(path)
  const url = URL.createObjectURL(blob)
  window.open(url, '_blank', 'noopener,noreferrer')
  window.setTimeout(() => URL.revokeObjectURL(url), 30_000)
}

export function ReviewQueuePage() {
  const queryClient = useQueryClient()
  const queue = useQuery({ queryKey:['reviewer-assignments'], queryFn:() => apiRequest<ReviewerAssignment[]>('/api/v1/reviewer/assignments') })
  const decide = useMutation({ mutationFn:({ verificationId, payload }:{ verificationId:number; payload:unknown }) => apiRequest(`/api/v1/reviewer/verifications/${verificationId}/decision`, { method:'POST', body:JSON.stringify(payload) }), onSuccess:() => queryClient.invalidateQueries({ queryKey:['reviewer-assignments'] }) })
  function submit(event:FormEvent<HTMLFormElement>, assignment:ReviewerAssignment) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const adjusted_scores = Object.fromEntries(assignment.ai_result.criteria.map((criterion) => [criterion.criterion, Number(data.get(`score_${criterion.criterion}`))]))
    decide.mutate({ verificationId:assignment.verification.id, payload:{ outcome:data.get('outcome'), reason:data.get('reason'), adjusted_scores } })
  }
  return <section className="workspace-page"><p className="eyebrow">EVIDENCE REVIEW QUEUE</p><h1>待复核证据</h1><p className="page-intro">依次核对作品原件、创作说明、动态答辩和量表证据。修改 AI 分值或作出决定时必须说明理由。</p>{queue.data?.map((assignment) => <article className="review-assignment" key={assignment.assignment_id}>
    <header><div><span>复核记录 #{assignment.verification.id}</span><h2>{assignment.evidence.title}</h2></div><span className="status-chip" data-status={assignment.verification.status}>{verificationLabels[assignment.verification.status]}</span></header>
    {assignment.evidence.file_type.startsWith('image/') ? <SecureImage src={assignment.evidence.file_url} alt={assignment.evidence.title} /> : <button className="document-preview" type="button" onClick={() => openEvidence(assignment.evidence.file_url)}>打开作品原文件</button>}
    <dl className="evidence-details"><div><dt>创作背景</dt><dd>{assignment.evidence.creation_context}</dd></div><div><dt>本人职责</dt><dd>{assignment.evidence.personal_role}</dd></div><div><dt>制作过程</dt><dd>{assignment.evidence.process_description}</dd></div><div><dt>迭代说明</dt><dd>{assignment.evidence.iteration_notes}</dd></div></dl>
    <section className="defense-transcript"><h3>动态答辩</h3>{assignment.defense.map((item) => <article key={item.question_id}><b>{item.question}</b><p>{item.answer || '未回答'}</p></article>)}</section>
    <form className="review-decision-form" onSubmit={(event) => submit(event, assignment)}>
      <h3>{assignment.rubric_version || '分类证据'} 量表</h3>{assignment.ai_result.criteria.map((criterion) => <label className="rubric-input" key={criterion.criterion}><span>{criterion.criterion}</span><input name={`score_${criterion.criterion}`} type="number" min="0" max="4" defaultValue={criterion.score} required /><small>{criterion.evidence.map((item) => `${item.reference}：${item.reason}`).join('；')}</small></label>)}
      <label>人工决定<select name="outcome" required>{outcomes.map(([value,label]) => <option value={value} key={value}>{label}</option>)}</select></label>
      <label>决定与调分理由<textarea name="reason" required minLength={2} placeholder="说明你采信了哪些证据，以及与 AI 初评不同之处" /></label>
      <button className="primary-button" disabled={decide.isPending}>提交人工复核</button>
      {decide.isError && <p className="form-error">{decide.error.message}</p>}
    </form>
  </article>)}{!queue.isLoading && !queue.data?.length && <div className="empty-inline">暂无分配给你的复核任务</div>}</section>
}
