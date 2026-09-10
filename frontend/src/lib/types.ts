export type UserRole = 'student' | 'requester' | 'reviewer' | 'admin'
export type EvidenceVisibility = 'private' | 'project_only' | 'public'
export type AssessmentStatus = 'queued' | 'running' | 'succeeded' | 'failed'
export type AssessmentStage = 'observation' | 'reassessment'
export type VerificationStatus = 'pending_human_review' | 'verified' | 'more_evidence' | 'rejected' | 'revoked'

export interface User { id:number; username:string; email:string; role:UserRole; school:string|null; college:string|null; major:string|null; grade:string|null; is_active:boolean }
export interface TokenResponse { access_token:string; token_type:'bearer' }
export interface Project { id:number; creator_id:number; title:string; description:string; category:string; budget:string|null; deadline:string; audit_status:string; lifecycle_status:string; required_skills:string[]; deliverables:string|null; acceptance_criteria:string|null; created_at:string }
export interface ProjectPage { items:Project[]; total:number; page:number; page_size:number }
export interface Skill { id:number; user_id:number; name:string; description:string|null; growth_score:number; level:number; created_at:string }

export interface Portfolio {
  id:number; user_id:number; skill_id:number; title:string; description:string|null; file_url:string; file_type:string
  evidence_type:string; creation_context:string|null; personal_role:string|null; process_description:string|null
  iteration_notes:string|null; visibility:EvidenceVisibility; related_skill_ids:number[]
  ai_processing_consent_at:string|null; ai_supported:boolean; created_at:string
}

export interface StudentProfile { user_id:number; username:string; display_name:string; avatar_url:string|null; bio:string|null; school:string|null; college:string|null; major:string|null; grade:string|null; skills:Skill[]; portfolios:Portfolio[] }
export interface Review { id:number; project_id:number; student_id:number; skill_score:number; communication_score:number; delivery_score:number; time_management_score:number; comment:string|null; created_at:string }
export interface EvidenceReference { source:'image_region'|'work_description'|'defense_answer'; reference:string; reason?:string }
export interface DefenseQuestion { id:number; position:number; text:string; targets_gap:string; answer:string|null; answered_at:string|null }
export interface RubricCriterion { criterion:string; score:number; evidence:EvidenceReference[] }

export interface AssessmentRun {
  id:number; run_number:string; portfolio_id:number; student_id:number; stage:AssessmentStage; status:AssessmentStatus
  model:string; rubric_version:string; input_summary:Record<string,unknown>
  structured_result:{ observable_facts?:Array<{observation:string;evidence:EvidenceReference}>; evidence_gaps?:string[]; criteria?:RubricCriterion[]; total_score?:number; review_status?:string; result_label?:string }|null
  error:string|null; source_run_id:number|null; retry_of_id:number|null; created_at:string; started_at:string|null; finished_at:string|null
  questions:DefenseQuestion[]; status_history:Array<{to_status:AssessmentStatus;created_at:string}>; result_label:string
}

export interface Credential { name:string; credential_number:string; qr_url:string; issued_at:string; status:'active'|'revoked' }
export interface Verification { id:number; assessment_run_id:number; student_id:number; portfolio_id:number; skill_id:number; status:VerificationStatus; human_result:{criteria?:RubricCriterion[];total_score?:number;human_review_reason?:string}|null; credential:Credential|null; created_at:string; updated_at:string }
export interface ApplicantSummary { user_id:number; display_name:string; skills:Skill[] }
export interface AuthorizedPortfolio extends Portfolio { ai_assessment:{criteria?:RubricCriterion[];total_score?:number}|null; verification_status:VerificationStatus|null; result_label:string|null }
export interface Application { id:number; project_id:number; student_id:number; message:string|null; status:'pending'|'accepted'|'rejected'|'finished'; created_at:string; student?:ApplicantSummary; authorized_portfolios?:AuthorizedPortfolio[] }
export type InvitationStatus = 'pending'|'viewed'|'applied'
export interface ProjectInvitation { id:number; project_id:number; student_id:number; inviter_id:number; message:string|null; status:InvitationStatus; created_at:string; viewed_at:string|null; project:Project }
export interface ReviewerAssignment { assignment_id:number; verification:Verification; evidence:Portfolio; defense:Array<{question_id:number;question:string;answer:string|null}>; ai_result:{criteria:RubricCriterion[];total_score:number;result_label:string} }
export interface ProjectValidation { id:number; project_id:number; student_id:number; requester_id:number; project_title:string; deliverables:string|null; acceptance_criteria:string|null; required_skills:string[]; outcome:string; created_at:string }
export interface PublicCredential { name:string; credential_number:string; status:'active'|'revoked'; rubric_version:string; issuer:string; issued_at:string; revoked_at:string|null; evidence_summary:{title:string;evidence_type:string}; verified_result:{criteria?:RubricCriterion[];total_score?:number;human_review_reason?:string} }
