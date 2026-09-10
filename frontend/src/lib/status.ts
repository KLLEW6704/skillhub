import type { AssessmentStatus, EvidenceVisibility, UserRole, VerificationStatus } from './types'

const labels: Record<string, string> = {
  pending: '待处理', accepted: '已录用', rejected: '未通过', finished: '已完成', approved: '审核通过',
  recruiting: '招募中', in_progress: '进行中', awaiting_review: '待项目评价', completed: '已完成', closed: '已关闭',
  queued: '排队中', running: '评估中', succeeded: 'AI 初评完成', failed: '评估失败',
  pending_human_review: '待人工复核', verified: '已核验', more_evidence: '补充材料', revoked: '已撤销',
}

export function statusLabel(status: string): string { return labels[status] ?? status }
export const roleLabels: Record<UserRole, string> = { student:'学生', requester:'项目方', reviewer:'评审', admin:'管理员' }
export const visibilityLabels: Record<EvidenceVisibility, string> = { private:'仅自己可见', project_only:'仅授权项目可见', public:'公开展示' }
export const assessmentLabels: Record<AssessmentStatus, string> = { queued:'排队中', running:'评估中', succeeded:'AI 初评完成', failed:'评估失败' }
export const verificationLabels: Record<VerificationStatus, string> = { pending_human_review:'待人工复核', verified:'已核验', more_evidence:'补充材料', rejected:'未通过', revoked:'已撤销' }
