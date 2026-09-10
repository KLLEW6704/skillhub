import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { apiRequest } from '../../lib/api'
import { verificationLabels } from '../../lib/status'
import type { User, Verification } from '../../lib/types'

export function VerificationsPage() {
  const queryClient = useQueryClient()
  const [reviewers, setReviewers] = useState<Record<number, number>>({})
  const verifications = useQuery({ queryKey:['admin-verifications'], queryFn:() => apiRequest<Verification[]>('/api/v1/admin/verifications') })
  const users = useQuery({ queryKey:['admin-users'], queryFn:() => apiRequest<User[]>('/api/v1/admin/users') })
  const assign = useMutation({ mutationFn:({ verificationId, reviewerId }:{ verificationId:number; reviewerId:number }) => apiRequest(`/api/v1/admin/verifications/${verificationId}/assign`, { method:'POST', body:JSON.stringify({ reviewer_id:reviewerId }) }), onSuccess:() => queryClient.invalidateQueries({ queryKey:['admin-verifications'] }) })
  const available = users.data?.filter((user) => user.role === 'reviewer' && user.is_active) ?? []
  return <section className="workspace-page"><p className="eyebrow">HUMAN REVIEW CONTROL</p><h1>人工复核分配</h1><p className="page-intro">AI 结果只有进入人工复核并获得通过，才可能生成 SkillHub 试行技能徽章。</p>{verifications.data?.map((verification) => <article className="manage-card" key={verification.id}><div><span>复核记录 #{verification.id}</span><h2>作品证据 #{verification.portfolio_id}</h2><p>{verificationLabels[verification.status]}</p></div>{verification.status === 'pending_human_review' && <div className="manage-actions"><select aria-label={`选择复核记录 ${verification.id} 的评审`} value={reviewers[verification.id] ?? ''} onChange={(event) => setReviewers({ ...reviewers, [verification.id]:Number(event.target.value) })}><option value="">选择评审</option>{available.map((reviewer) => <option value={reviewer.id} key={reviewer.id}>{reviewer.username}</option>)}</select><button disabled={!reviewers[verification.id] || assign.isPending} onClick={() => assign.mutate({ verificationId:verification.id, reviewerId:reviewers[verification.id] })}>分配</button></div>}</article>)}</section>
}
