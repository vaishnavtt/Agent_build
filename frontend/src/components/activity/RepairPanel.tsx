import React, { useEffect, useRef, useState } from 'react';
import { Wrench } from 'lucide-react';
import { ElevatedButton } from '../common/ElevatedButton';
import {
  getRepairReadiness, hasVerifiedCandidate, outcomeTitle, requestRepair,
  type RepairOutcome, type RepairReadiness, type RepairScope,
} from './repairApi';

const fields = {
  workflow_id: 'Workflow ID',
  workflow_revision_id: 'Workflow revision ID',
  execution_run_id: 'Execution run ID',
} as const;
const initialScope = { workflow_id: '', workflow_revision_id: '', execution_run_id: '' };
const readable = (label: string) => label.replaceAll('_', ' ');

export function RepairPanel() {
  const [scope, setScope] = useState<RepairScope>(initialScope);
  const [ready, setReady] = useState<RepairReadiness | null>(null);
  const [outcome, setOutcome] = useState<RepairOutcome | null>(null);
  const [error, setError] = useState('');
  const [pending, setPending] = useState<'diagnose' | 'recover' | null>(null);
  const busy = useRef(false);
  const scopeComplete = Object.values(scope).every(value => value.trim());

  useEffect(() => {
    const controller = new AbortController();
    getRepairReadiness(controller.signal).then(setReady).catch(() => {
      if (!controller.signal.aborted) setError('Could not reach the repair service. Try refreshing readiness.');
    });
    return () => controller.abort();
  }, []);

  async function refresh() {
    setError('');
    try {
      setReady(await getRepairReadiness());
    } catch {
      setReady(null);
      setError('Could not reach the repair service.');
    }
  }

  async function submit(action: 'diagnose' | 'recover') {
    if (busy.current || !scopeComplete) return;
    busy.current = true;
    setPending(action);
    setError('');
    setOutcome(null);
    try {
      const result = await requestRepair(action, scope);
      setOutcome(result);
      if (result.readiness) setReady(result.readiness);
    } catch {
      setError('The repair request could not be completed. Check the backend connection and try again.');
    } finally {
      busy.current = false;
      setPending(null);
    }
  }

  return (
    <section id="workflow-repair" aria-labelledby="repair-title"
      className="p-6 sm:p-7 rounded-3xl border border-[#CF8047]/40 bg-[#FAF5F1] shadow-card space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="repair-title" className="flex items-center gap-2 font-extrabold text-[#111111]">
          <Wrench className="w-4 h-4 text-[#B15F2C]" /> Workflow repair
        </h2>
        <button type="button" disabled={!!pending} onClick={() => void refresh()}
          className="text-xs font-semibold text-[#B15F2C] underline disabled:opacity-45">
          Refresh readiness
        </button>
      </div>
      <div aria-live="polite" className="text-sm text-[#555555] space-y-1">
        {ready ? (
          <>
            <p>{ready.recovery_available ? 'Production recovery is ready.' : 'Production recovery dependencies are unavailable.'}</p>
            {!!ready.blockers.length && (
              <p className="text-xs">{ready.blockers.map(key => `${readable(key)} (${readable(ready.dependencies[key] ?? 'unavailable')})`).join(', ')}</p>
            )}
          </>
        ) : !error && <p>Checking repair readiness…</p>}
      </div>

      {ready?.diagnosis_available && (
        <form className="space-y-3" onSubmit={event => { event.preventDefault(); void submit('diagnose'); }}>
          <p className="text-xs text-[#555555]">Enter the backend identifiers for a recorded failure.</p>
          <div className="grid gap-3 sm:grid-cols-3">
            {(Object.keys(fields) as (keyof RepairScope)[]).map(key => (
              <label key={key} className="block text-xs font-semibold text-[#111111]">
                {fields[key]}
                <input value={scope[key]} disabled={!!pending} required maxLength={128}
                  onChange={event => { setOutcome(null); setScope(previous => ({ ...previous, [key]: event.target.value })); }}
                  className="mt-1 w-full rounded-lg border border-[#EAE8E5] bg-white p-2 font-normal"
                />
              </label>
            ))}
          </div>
          <div className="flex flex-wrap gap-2">
            <ElevatedButton type="submit" variant="secondary" size="sm" disabled={!!pending || !scopeComplete}>
              Diagnose failure
            </ElevatedButton>
            <ElevatedButton type="button" variant="primary" size="sm"
              disabled={!!pending || !scopeComplete || !ready.recovery_available} onClick={() => void submit('recover')}>
              Plan and recover
            </ElevatedButton>
          </div>
        </form>
      )}
      {pending && <p role="status" className="text-sm">{pending === 'diagnose' ? 'Diagnosing the recorded failure…' : 'Waiting for the recovery result…'}</p>}
      {error && <p role="alert" className="text-sm text-rose-800">{error}</p>}

      {outcome && (
        <div aria-live="polite" className="rounded-2xl bg-white border border-[#EAE8E5] p-4 space-y-3 text-sm">
          <h3 className="font-extrabold">{outcomeTitle(outcome)}</h3>
          <p>{outcome.explanation}</p>
          {outcome.diagnosis && (
            <div className="text-xs space-y-1">
              {outcome.diagnosis_status === 'advisory' && <p className="font-semibold">AI advisory · Human review required</p>}
              <p>Failure category: {readable(outcome.diagnosis.category)}</p>
              {outcome.diagnosis.affected_node_id && <p>Affected node: {outcome.diagnosis.affected_node_id}</p>}
              {outcome.diagnosis.affected_configuration_field && <p>Field: {outcome.diagnosis.affected_configuration_field}</p>}
              {outcome.diagnosis.root_cause !== outcome.explanation && <p>{outcome.diagnosis.root_cause}</p>}
              {outcome.diagnosis.requires_human_intervention && outcome.diagnosis_status !== 'advisory' && <p>Human intervention required</p>}
            </div>
          )}
          <p className="text-xs">Attempts: {outcome.attempts?.length ?? 0} of {ready?.max_attempts ?? 2}</p>
          {outcome.retry_stop && <p className="text-xs">Retry ended: {readable(outcome.retry_stop)}</p>}
          {outcome.attempts?.map(attempt => (
            <div key={attempt.number} className="border-t border-[#EAE8E5] pt-2 text-xs space-y-1">
              <p className="font-semibold">Attempt {attempt.number} · {readable(attempt.status)}</p>
              <p>Proposed correction: restore {attempt.proposal.field_name} on {attempt.proposal.node_id}.</p>
              {attempt.candidate && <p>Candidate created · {attempt.candidate.revision_id}</p>}
              <p>Verification: {hasVerifiedCandidate(attempt) ? 'verified'
                : attempt.verification_status === 'failed' ? 'failed' : 'pending or unavailable'}</p>
              {attempt.verification?.failed_test_reruns.map(test => <p key={test.test_id}>Failed-test rerun {test.test_id}: {readable(test.status)}</p>)}
              {attempt.verification?.regression_test_reruns.map(test => <p key={test.test_id}>Regression {test.test_id}: {readable(test.status)}</p>)}
              <p>{attempt.explanation}</p>
            </div>
          ))}
          {outcome.promotion && <p className="text-xs">Promotion: {outcome.promotion === 'confirmed'
            ? hasVerifiedCandidate(outcome.attempts?.at(-1)) ? 'confirmed' : 'unverified response'
            : readable(outcome.promotion)}</p>}
          {outcome.rollback && outcome.rollback !== 'not_required' && <p className="text-xs">Rollback: {outcome.rollback === 'restored'
            ? outcome.restored_revision?.revision_id ? 'restored' : 'unconfirmed'
            : readable(outcome.rollback)}</p>}
        </div>
      )}
    </section>
  );
}
