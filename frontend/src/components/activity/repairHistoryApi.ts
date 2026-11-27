import type { RepairOutcome, RepairScope } from './repairApi';

export interface HistoryRecord extends Omit<RepairOutcome, 'explanation'> {
  recovery_id: string;
  category: string | null;
  timestamp: string | null;
  duration_ms: number | null;
  provider_calls: number | null;
}

export type HistoryState =
  | { message: string }
  | { records: HistoryRecord[]; next: number | null };

export async function loadHistory(scope: RepairScope, offset: number, signal: AbortSignal): Promise<HistoryState> {
  const query = new URLSearchParams({ workflow_id: scope.workflow_id, workflow_revision_id: scope.workflow_revision_id,
    execution_run_id: scope.execution_run_id, offset: String(offset), limit: '10' });
  const response = await fetch('/api/v1/repair/history?' + query, { signal, cache: 'no-store' });
  if (!response.ok) {
    const messages: Record<number, string> = {
      401: 'Sign in to view repair history.', 403: 'Access to this history was denied.',
      404: 'The failed execution could not be found.', 409: 'The selected revision is stale.',
    };
    const error = await response.json().catch(() => ({}));
    return { message: messages[response.status] ?? (error?.status === 'history_evidence_unavailable'
      ? 'The stored repair evidence could not be verified.' : 'Repair history is unavailable.') };
  }
  const body = await response.json();
  if (!body.scope || !Object.entries(scope).every(([key, value]) => body.scope[key] === value)
    || !Array.isArray(body.records) || body.records.length > 10
    || !(body.next_offset === null || body.next_offset === offset + 10)) {
    throw new Error('Invalid history scope or page.');
  }
  const records = body.records.map((item: HistoryRecord & { restored_revision_id?: string }) => {
    if (!item.recovery_id || typeof item.status !== 'string' || !Array.isArray(item.attempts)
      || item.attempts.length > 2) throw new Error('Invalid history record.');
    for (const attempt of item.attempts) {
      if (!attempt?.proposal || typeof attempt.proposal.operation !== 'string' || typeof attempt.status !== 'string')
        throw new Error('Invalid stored attempt.');
      const v = attempt.verification;
      if (v && (!Array.isArray(v.failed_test_reruns) || !Array.isArray(v.regression_test_reruns)
        || [...v.failed_test_reruns, ...v.regression_test_reruns].some(t => !t || typeof t.test_id !== 'string')))
        throw new Error('Invalid stored verification.');
    }
    return { ...item, restored_revision: item.restored_revision_id ? { revision_id: item.restored_revision_id } : null };
  });
  return { records, next: body.next_offset };
}
