import { useEffect, useState } from 'react';
import { outcomeTitle, type RepairScope } from './repairApi';
import { loadHistory, type HistoryState } from './repairHistoryApi';

function HistoryPage({ scope, offset, setOffset }: { scope: RepairScope; offset: number; setOffset: (n: number) => void }) {
  const [state, setState] = useState<HistoryState>({ message: 'Loading repair history…' });
  const { workflow_id, workflow_revision_id, execution_run_id } = scope;
  useEffect(() => {
    const controller = new AbortController();
    loadHistory({ workflow_id, workflow_revision_id, execution_run_id }, offset, controller.signal)
      .then(value => { if (!controller.signal.aborted) setState(value); })
      .catch(() => { if (!controller.signal.aborted) setState({ message: 'Could not load the repair history. Check the connection and reload.' }); });
    return () => controller.abort();
  }, [workflow_id, workflow_revision_id, execution_run_id, offset]);

  return <div className="space-y-3 text-sm" aria-live="polite">
    <p>Workflow {workflow_id} · Revision {workflow_revision_id} · Failed execution {execution_run_id}</p>
    {'message' in state ? <p>{state.message}</p> : <>
      {!state.records.length && <p>No recovery has been recorded for this execution.</p>}
      {state.records.map(row => <article key={row.recovery_id} className="rounded-xl border bg-white p-3 space-y-1">
        <h4 className="font-semibold">{outcomeTitle(row)}</h4>
        <p>Recovery {row.recovery_id} · {row.category ?? 'Diagnosis unavailable'} · Attempts {row.attempts?.length}</p>
        {row.timestamp && <time dateTime={row.timestamp}>{row.timestamp}</time>}
        {row.duration_ms != null && <p>Duration {row.duration_ms} ms</p>}
        {row.provider_calls != null && <p>Provider calls {row.provider_calls}</p>}
        {row.attempts?.map(a => <div key={a.number} className="border-t pt-2 text-xs">
          <p>Attempt {a.number} · {a.proposal.operation.replaceAll('_', ' ')} · {a.proposal.node_id} / {a.proposal.field_name}</p>
          <p>Candidate {a.candidate?.revision_id ?? 'unavailable'} · {a.status.replaceAll('_', ' ')}</p>
          <p>Structure {a.verification?.structural_validation ?? 'unavailable'} · Execution {a.verification?.execution?.run_id ?? 'unavailable'} {a.verification?.execution?.status}</p>
          {a.verification?.failed_test_reruns.map(t => <p key={t.test_id}>Failed-test rerun {t.test_id} · {t.status}</p>)}
          {a.verification?.regression_test_reruns.map(t => <p key={t.test_id}>Regression {t.test_id} · {t.status}</p>)}
        </div>)}
      </article>)}
      {state.next !== null && <button onClick={() => setOffset(state.next!)}>Older recoveries</button>}
    </>}
    {offset > 0 && <button onClick={() => setOffset(Math.max(0, offset - 10))}>Newer recoveries</button>}
  </div>;
}

export function RepairHistory({ scope }: { scope?: RepairScope }) {
  return <ScopedHistory key={JSON.stringify(scope)} scope={scope} />;
}

function ScopedHistory({ scope }: { scope?: RepairScope }) {
  const [offset, setOffset] = useState(0);
  return <section className="space-y-2" aria-label="Repair history">
    <h3 className="text-sm font-semibold">Repair history</h3>
    {scope ? <HistoryPage key={offset} scope={scope} offset={offset} setOffset={setOffset} />
      : <p className="text-sm">History is unavailable until the execution monitor supplies a verified failed execution.</p>}
  </section>;
}
