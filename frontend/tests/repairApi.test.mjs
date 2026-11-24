import assert from 'node:assert/strict';
import { test } from 'node:test';
import { outcomeTitle, requestRepair } from '../src/components/activity/repairApi.ts';

const passed = {
  status: 'verified',
  verification_status: 'passed',
  candidate: { revision_id: 'candidate' },
  verification: {
    candidate_revision_id: 'candidate',
    structural_validation: 'passed',
    execution: { status: 'passed', run_id: 'candidate-run' },
    required_failed_test_ids: ['original'],
    required_regression_test_ids: ['regression'],
    failed_test_reruns: [{ test_id: 'original', status: 'passed' }],
    regression_test_reruns: [{ test_id: 'regression', status: 'passed' }],
  },
};

test('promotion requires both candidate evidence and confirmation', () => {
  const result = { status: 'promoted', promotion: 'confirmed', attempts: [passed] };
  assert.equal(outcomeTitle(result), 'Promotion confirmed');
  assert.equal(outcomeTitle({ ...result, promotion: null }), 'Verified candidate');
  assert.equal(outcomeTitle({ ...result, attempts: [] }), 'Verification evidence unavailable');
  assert.equal(outcomeTitle({
    ...result,
    attempts: [{ ...passed, verification: { ...passed.verification, regression_test_reruns: [] } }],
  }), 'Verification evidence unavailable');
});

test('rollback requires confirmation and restored revision', () => {
  assert.equal(outcomeTitle({ status: 'rolled_back', rollback: 'not_required' }), 'Rollback could not be confirmed');
  assert.equal(outcomeTitle({
    status: 'rolled_back', rollback: 'restored', restored_revision: { revision_id: 'previous' },
  }), 'Rollback confirmed');
});

test('requests send identifiers only and preserve structured unavailable responses', async t => {
  const scope = {
    workflow_id: 'workflow', workflow_revision_id: 'revision', execution_run_id: 'run',
  };
  const response = { status: 'dependencies_unavailable', explanation: 'No verifier.' };
  t.mock.method(globalThis, 'fetch', async (path, options) => {
    assert.equal(path, '/api/v1/repair/recover');
    assert.deepEqual(JSON.parse(options.body), scope);
    return { ok: false, json: async () => response };
  });
  assert.deepEqual(await requestRepair('recover', { ...scope, trusted: 'ignored' }), response);
});

test('network failures and malformed responses are rejected', async t => {
  const scope = { workflow_id: 'workflow', workflow_revision_id: 'revision', execution_run_id: 'run' };
  const mock = t.mock.method(globalThis, 'fetch', async () => { throw new Error('network issue'); });
  await assert.rejects(requestRepair('diagnose', scope));
  mock.mock.mockImplementation(async () => ({ ok: true, json: async () => ({}) }));
  await assert.rejects(requestRepair('diagnose', scope), /Invalid repair response/);
});
