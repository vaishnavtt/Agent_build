export interface RepairScope {
  workflow_id: string;
  workflow_revision_id: string;
  execution_run_id: string;
}

type VerificationStatus = 'not_run' | 'passed' | 'failed';
type TestResult = { test_id: string; status: VerificationStatus };

export interface RepairReadiness {
  diagnosis_available: boolean;
  recovery_available: boolean;
  max_attempts: number;
  dependencies: Record<string, string>;
  blockers: string[];
}

interface Verification {
  candidate_revision_id: string;
  structural_validation: VerificationStatus;
  execution: { run_id: string; status: VerificationStatus } | null;
  required_failed_test_ids: string[];
  required_regression_test_ids: string[];
  failed_test_reruns: TestResult[];
  regression_test_reruns: TestResult[];
}

interface RepairAttempt {
  number: number;
  status: string;
  proposal: { node_id: string; field_name: string; operation: string };
  candidate: { revision_id: string } | null;
  verification: Verification | null;
  verification_status: VerificationStatus;
  explanation: string;
}

export interface RepairOutcome {
  status: string;
  explanation: string;
  readiness?: RepairReadiness | null;
  diagnosis?: {
    category: string;
    affected_node_id: string | null;
    affected_configuration_field: string | null;
    root_cause: string;
    requires_human_intervention: boolean;
  } | null;
  diagnosis_status?: string | null;
  attempts?: RepairAttempt[];
  promotion?: string | null;
  rollback?: string;
  restored_revision?: { revision_id: string } | null;
  retry_stop?: string | null;
}

export async function getRepairReadiness(signal?: AbortSignal): Promise<RepairReadiness> {
  const response = await fetch('/api/v1/repair/readiness', { signal });
  if (!response.ok) throw new Error('Could not load repair readiness.');
  const body: RepairReadiness = await response.json();
  if (typeof body?.diagnosis_available !== 'boolean' || typeof body.recovery_available !== 'boolean'
    || !Array.isArray(body.blockers) || !body.dependencies) {
    throw new Error('Invalid readiness response.');
  }
  return body;
}

export async function requestRepair(action: 'diagnose' | 'recover', scope: RepairScope): Promise<RepairOutcome> {
  const response = await fetch(`/api/v1/repair/${action}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      workflow_id: scope.workflow_id,
      workflow_revision_id: scope.workflow_revision_id,
      execution_run_id: scope.execution_run_id,
    }),
  });
  const body: RepairOutcome = await response.json();
  if (typeof body?.status !== 'string' || typeof body.explanation !== 'string'
    || (body.attempts !== undefined && !Array.isArray(body.attempts))) {
    throw new Error('Invalid repair response.');
  }
  return body;
}

function allTestsPassed(ids: string[], results: TestResult[]): boolean {
  return Array.isArray(ids) && Array.isArray(results) && new Set(ids).size === ids.length
    && results.length === ids.length
    && ids.every(id => results.some(result => result.test_id === id && result.status === 'passed'));
}

export function hasVerifiedCandidate(attempt: RepairAttempt | undefined): boolean {
  const evidence = attempt?.verification;
  return !!evidence && attempt.status === 'verified' && attempt.verification_status === 'passed'
    && !!attempt.candidate?.revision_id && attempt.candidate.revision_id === evidence.candidate_revision_id
    && !!evidence.execution?.run_id && evidence.structural_validation === 'passed' && evidence.execution?.status === 'passed'
    && allTestsPassed(evidence.required_failed_test_ids, evidence.failed_test_reruns)
    && allTestsPassed(evidence.required_regression_test_ids, evidence.regression_test_reruns);
}

const titles: Record<string, string> = {
  deterministic: 'Diagnosis completed',
  advisory: 'AI advisory available',
  human_review: 'Human intervention required',
  unresolved: 'Unresolved failure',
  dependencies_unavailable: 'Repair dependencies unavailable',
  snapshot_unavailable: 'Original snapshot unavailable',
  attempt_reservation_blocked: 'Attempt reservation unavailable',
  attempt_limit_reached: 'Attempt limit reached',
  application_failed: 'Candidate could not be created',
  plan_blocked: 'Repair planning blocked',
  verification_unavailable: 'Candidate verification pending',
  repair_failed: 'Repair failed',
  rollback_failed: 'Rollback could not be confirmed',
  promotion_failed: 'Promotion could not be confirmed',
  revision_conflict: 'Workflow revision changed',
  duplicate_request: 'Recovery already requested',
  failure_not_found: 'Recorded failure not found',
  forbidden: 'Access denied',
  invalid_request: 'Invalid repair request',
  invalid_context: 'Failure context could not be confirmed',
  provider_unavailable: 'Advisory provider unavailable',
  response_rejected: 'Advisory response could not be validated',
  graph_error: 'Recovery stopped',
};

export function outcomeTitle(outcome: Pick<RepairOutcome, 'status' | 'attempts' | 'promotion' | 'rollback' | 'restored_revision'>): string {
  if (outcome.status === 'promoted' || outcome.status === 'verified_pending_promotion') {
    if (!hasVerifiedCandidate(outcome.attempts?.at(-1))) return 'Verification evidence unavailable';
    return outcome.status === 'promoted' && outcome.promotion === 'confirmed'
      ? 'Promotion confirmed' : 'Verified candidate';
  }
  if (outcome.status === 'rolled_back') {
    return outcome.rollback === 'restored' && outcome.restored_revision?.revision_id
      ? 'Rollback confirmed' : 'Rollback could not be confirmed';
  }
  return titles[outcome.status] ?? 'Repair result';
}
