/**
 * Workflow / approvals API layer.
 *
 * The workflow **engine** is generic and configuration-driven: a definition
 * describes the approval shape (sequential / parallel + ordered approvers), an
 * instance tracks one entity through the standard state set, and each step
 * records an approver's decision. No business approval rule (thresholds, which
 * document routes to whom) is encoded here — that stays server-side
 * configuration (see do-not-build-yet #7, "engine may be built; rules must not
 * be hard-coded").
 *
 * This layer covers the pieces an approver needs: the personal inbox
 * (`/workflow/instances/mine/`) and the two self-service transitions. The
 * decision endpoint is self-guarding on the server (only an assigned,
 * still-pending approver may act); cancelling requires `workflow.instance.manage`.
 */
import { apiClient } from './client';

/** Approval shape of a definition (mirrors ``ApprovalMode``). */
export type ApprovalMode = 'SEQUENTIAL' | 'PARALLEL';

/**
 * A workflow *definition* — engine configuration describing an approval shape.
 * `config` is free-form JSON interpreted by callers; no business routing rule
 * is encoded here (do-not-build-yet #7).
 */
export interface WorkflowDefinition {
  id: string;
  code: string;
  name_en: string;
  name_fa: string;
  approval_mode: ApprovalMode;
  config: Record<string, unknown>;
  is_active: boolean;
}

/** Create a workflow definition (audited write; `code` is unique). */
export function createWorkflowDefinition(
  payload: Partial<WorkflowDefinition>,
): Promise<WorkflowDefinition> {
  return apiClient.post<WorkflowDefinition>('/workflow/definitions/', payload);
}

/** Instance lifecycle (mirrors ``WorkflowState``). */
export type WorkflowState =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'APPROVED'
  | 'REJECTED'
  | 'CANCELLED';

/** Per-approver decision on a step (mirrors ``StepDecision``). */
export type StepDecision = 'PENDING' | 'APPROVED' | 'REJECTED';

/** One approver's slot in an instance. */
export interface ApprovalStep {
  id: string;
  sequence: number;
  approver: string;
  decision: StepDecision;
  comment: string;
  decided_at: string | null;
}

/** One entity's journey through an approval definition. */
export interface WorkflowInstance {
  id: string;
  definition: string;
  entity_type: string;
  entity_id: string;
  state: WorkflowState;
  steps: ApprovalStep[];
  created_at: string;
}

/** Approve or reject an instance the caller is an assigned approver on. */
export function recordDecision(
  id: string,
  approve: boolean,
  comment = '',
): Promise<WorkflowInstance> {
  return apiClient.post<WorkflowInstance>(`/workflow/instances/${id}/decision/`, {
    approve,
    comment,
  });
}

/** Cancel an in-flight instance (requires ``workflow.instance.manage``). */
export function cancelWorkflow(id: string, reason = ''): Promise<WorkflowInstance> {
  return apiClient.post<WorkflowInstance>(`/workflow/instances/${id}/cancel/`, {
    reason,
  });
}
