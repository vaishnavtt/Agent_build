import assert from 'node:assert/strict';
import { test } from 'node:test';
import { loadHistory } from '../src/components/activity/repairHistoryApi.ts';
import { outcomeTitle } from '../src/components/activity/repairApi.ts';

const scope = { workflow_id: 'wf', workflow_revision_id: 'rev', execution_run_id: 'run' };
const read = () => loadHistory(scope, 0, new AbortController().signal);
for (const [code, label] of [[403, 'denied'], [404, 'found'], [409, 'stale'], [503, 'unavailable']]) {
  test('history HTTP ' + code, async t => {
    t.mock.method(globalThis, 'fetch', async () => new Response('{}', { status: code }));
    assert.match((await read()).message, new RegExp(label));
  });
}

test('history rejects network failures, mismatched scope and malformed attempt evidence', async t => {
  const fetch = t.mock.method(globalThis, 'fetch', async () => { throw Error('offline'); });
  await assert.rejects(read(), /offline/);
  fetch.mock.mockImplementation(async () => Response.json({ scope: { ...scope, execution_run_id: 'other' }, records: [], next_offset: null }));
  await assert.rejects(read(), /scope/);
  fetch.mock.mockImplementation(async () => Response.json({ scope, records: [{ recovery_id: 'r', status: 'promoted', attempts: [{}] }], next_offset: null }));
  await assert.rejects(read(), /attempt/);
});

test('stored history distinguishes empty pages, false success and rollback evidence', async t => {
  const page = { scope, records: [], next_offset: null };
  t.mock.method(globalThis, 'fetch', async () => Response.json(page));
  assert.deepEqual(await read(), { records: [], next: null });
  page.records = [{ recovery_id: 'r', attempts: [], status: 'promoted', promotion: 'confirmed' }];
  assert.equal(outcomeTitle((await read()).records[0]), 'Verification evidence unavailable');
  Object.assign(page.records[0], { status: 'rolled_back', rollback: 'restored' });
  assert.equal(outcomeTitle((await read()).records[0]), 'Rollback could not be confirmed');
  page.records[0].restored_revision_id = 'working';
  assert.equal(outcomeTitle((await read()).records[0]), 'Rollback confirmed');
});
