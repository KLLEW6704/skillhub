import { useQuery } from '@tanstack/react-query'
import { apiRequest } from '../../lib/api'
import { assessmentLabels } from '../../lib/status'
import type { AssessmentRun } from '../../lib/types'

export function AssessmentRunsPage() {
  const runs = useQuery({ queryKey:['admin-assessment-runs'], queryFn:() => apiRequest<AssessmentRun[]>('/api/v1/admin/assessment-runs') })
  return <section className="workspace-page"><p className="eyebrow">MODEL RUN AUDIT</p><h1>AI 运行记录</h1><p className="page-intro">这里展示运行编号、模型、状态、失败原因和时间。系统永远不会在页面中显示 API Key。</p><div className="audit-table" role="table"><div className="audit-row" role="row"><b>运行编号 / 阶段</b><b>状态 / 模型</b><b>时间 / 错误</b></div>
    {runs.data?.map((run) => <article className="audit-row" key={run.id} role="row"><div><b>{run.run_number}</b><span>{run.stage === 'observation' ? '图片观察' : '答辩复评'} · {run.rubric_version}</span></div><div><span className={`status-chip ${run.status}`}>{assessmentLabels[run.status]}</span><small>模型：{run.model}</small></div><div><span>{run.started_at ? new Date(run.started_at).toLocaleString() : '尚未开始'}</span>{run.error && <p className="form-error">{run.error}</p>}</div></article>)}
  </div>{!runs.isLoading && !runs.data?.length && <div className="empty-inline">暂无 AI 运行记录</div>}</section>
}
