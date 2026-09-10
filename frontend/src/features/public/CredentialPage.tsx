import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { apiRequest } from '../../lib/api'
import type { PublicCredential } from '../../lib/types'

export function CredentialPage() {
  const { number } = useParams()
  const credential = useQuery({ queryKey:['credential', number], queryFn:() => apiRequest<PublicCredential>(`/api/v1/credentials/${number}`), retry:false })
  if (credential.isLoading) return <div className="page-state">核对试行技能徽章…</div>
  if (!credential.data) return <div className="page-state">没有找到这份核验记录</div>
  const item = credential.data
  return <section className="credential-page"><Link to="/talent" className="back-link">← 返回技能大厅</Link><article className={`credential-sheet ${item.status}`}><p className="eyebrow">PUBLIC VERIFICATION</p><span className="credential-state">{item.status === 'active' ? '记录有效' : '记录已撤销'}</span><h1>{item.name}</h1><b className="credential-number">{item.credential_number}</b><dl><div><dt>证据摘要</dt><dd>{item.evidence_summary.title}</dd></div><div><dt>量表版本</dt><dd>{item.rubric_version}</dd></div><div><dt>签发者</dt><dd>{item.issuer}</dd></div><div><dt>签发时间</dt><dd>{new Date(item.issued_at).toLocaleString()}</dd></div></dl><h2>核验结果</h2><div className="credential-rubric">{item.verified_result.criteria?.map((criterion) => <div key={criterion.criterion}><span>{criterion.criterion}</span><b>{criterion.score} / 4</b></div>)}</div><p className="boundary-note">这是 SkillHub 试行技能徽章，用于呈现平台内的作品证据与人工复核结果，不属于学历、文凭或学校官方认证。</p></article></section>
}
