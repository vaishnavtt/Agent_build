# Member 6 completion review

## A. Executive summary

November 27, 2026. Local review candidate on `feature/member6-self-repair`, based on published commit `66a7be6`. The previous audit scored 8.5/10. This review scores **9.5/10 (95%) for individual implementation**, **9/10 (90%) fully independently exercised within Member 6's boundary**, and **5% remaining assigned work**. The 90% verification score gives half credit each to the advisory provider group (offline behavior verified, live connectivity pending) and the execution UI group (fixture-server history verified, real execution selection pending). “Independent” here means exercised by a separate test or probe and is subject to team re-audit. Production recovery readiness is **0/12 required production bindings configured in this checkout**. The compiled LangGraph runtime is available separately. One real cross-branch structural service was verified in isolation. The default host supplies no authorized history reader.

| Original assessed responsibility | Previous → current | Evidence and external boundary |
|---|---|---|
| Trusted failure correlation | Full → full | Three-ID authorization and evidence matching in RepairService.run. Integration tests reject run/revision mismatch. Members 1 and 4 supply trusted identity and records. |
| Deterministic diagnosis | Full → full | RuleBasedDiagnoser recognizes published structural issue types and scoped node/edge evidence. Existing and new diagnosis/graph cases run offline. Member 3 must approve each policy. |
| Advisory Gemini | Full → full | Mock provider tests cover routing, sanitization, malformed replies and call counts. SDK import checked. External connectivity requires separate approval. |
| Safe operation coverage | Partial → full within the bounded module | Scalar planner plus graph_policy.prepare/apply. Missing edge and named-port restoration executed in fixtures. Owner policy and immutable working revision required before activation. |
| Snapshot/candidate isolation | Full → full | Original-state, stale digest, changed approval/criteria, no additional edits and after-reservation recheck tests. Member 1 supplies durable revisions. |
| Two attempts and orchestration | Full → full | Real compiled graph. Reservation, distinct correction, exhaustion and duplicate-claim tests. Cross-worker atomicity belongs to Member 1. |
| Failed and regression verification | Full → full | All four failing stages stop promotion. Actual Member 5 structural checker exercised independently. Member 5's immutable reruns and Member 4's trusted evidence remain outstanding. |
| Lifecycle and conflicts | Full → full | Fixtures exercise confirmed, unavailable and conflicting revision changes. Member 1 owns production transactions. |
| History and attempt reporting | Partial → full within the module | Authorized read contract, bounded endpoint, allowlisted projection and terminal evidence checks. Chrome reloaded stored fixture records from the FastAPI route. Durable production storage and retention belong to Member 1. |
| User-visible execution integration | Partial → partial | History panel accepts server-supplied scope and verifies response association. Chrome exercised scope changes and stale responses. The host monitor still needs an authenticated failed-run selection. |

Points use the previous rubric of 1, 0.5 or 0 per responsibility. Individual points measure the Member 6 side of each interface. The scores give no production deployment credit for fixtures.

## B. Four remaining tasks

| Task | Previous | Current | Verification | Blocker |
|---|---|---|---|---|
| Connection and mapping repair | Scalar only | Bounded named-edge and port policies implemented | Exact graph comparison, original retention, unsafe proposals and verified graph recovery | Member 3 policy and Member 1 working revision |
| Production evidence | Twelve unconfigured bindings | Optional structural bridge verified against Member 5 code | Valid and invalid candidate probes and rejection before execution | See binding inventory below |
| Persistent history presentation | Synchronous response only | Authorized read contract, API and scoped UI | Disk-backed synthetic records, real FastAPI route and Chrome reload | Member 1 durable reader and Member 4 selection |
| Provider, tests and documentation | Mocked baseline | Expanded test suite, SDK import and documentation verified | Commands below | Live smoke requires explicit authorization |

## C. Implementation

Member 3's published `WorkflowNodeSchema` exposes id, type, config, inputHandles and outputHandles. `WorkflowEdgeSchema` exposes id, source, target, sourceHandle, targetHandle and optional condition. The generator also copies port lists into config. Those lists do not define a general source-to-target transformation language. The seven canonical node types include Input, Output, LLM, Tool, Condition, Human Approval and Document Reader.

The graph policy supports one direct Input → Output public data transfer with exactly one declared port on each side. A connection grant restores a missing edge or an explicitly approved incorrect handle. A mapping grant restores the named field association on an existing edge. Source and target types must match. The internal layout identifier `member3-named-handles-v1` describes the reviewed representation. It is provisional and does not add a field to Member 3's workflow JSON. The authority authenticates exact public ports, policy, compatible schema, feedback code, failed run, node, edge, original digest and working revision. Complex topologies, conflicting identifiers, arbitrary patches, endpoint reassignment, type conversions, approval gates, conditional edges, external actions and unapproved fields are outside the implemented policy. Unknown error codes cannot authorize changes.

Member 5 publishes NO_PATH_TO_OUTPUT, INVALID_CONNECTION, INVALID_SOURCE_HANDLE and INVALID_TARGET_HANDLE. Its path issue alone does not identify the missing edge. A separate trusted source must supply that identity. Invalid endpoint direction requires human review. Member 5 has no separate agreed error taxonomy for generic missing/invalid mappings. The implementation uses published handle codes for named-port defects. The tests that inject a missing handle simulate an upstream defect with explicit evidence.

Before reservation, the planner checks the entire graph against the authenticated working graph with only the permitted difference reversed. After reservation it repeats the policy and provenance lookup, independently deserializes the original, changes the authorized edge and checks the entire resulting digest. Requirements, acceptance criteria, configurations, other nodes, and every other graph field must match. Gemini receives no graph grant. The same two-attempt counter, immutable baseline, verification, concurrency and lifecycle gates apply to all operations.

History uses GET /api/v1/repair/history with workflow_id, workflow_revision_id, execution_run_id, offset (default 0) and limit (default 20, maximum 50). The host checks the authenticated principal before lookup. HistorySource.read(request, scope, offset, limit) must reauthorize and resolve the exact failed execution. The service requests one extra row to detect another page. Records must be newest-first with stable ordering and unique IDs. A known run with no recoveries returns an empty page. Unknown scope returns 404, denial 403, stale revision 409, and absent or inconsistent evidence 503. Responses carry Cache-Control: no-store. Use transaction-consistent pages or an opaque snapshot cursor if concurrent inserts require stable traversal across requests.

The history projection includes safe attempt and operation references, candidate revision and run, original test reruns, status, confirmed lifecycle references, and available timestamp, duration and provider metrics. Private free-text diagnostics, raw provider text, original/replacement values and graphs are excluded. Missing metrics stay null. The panel reads history only from its selected failed-execution prop; editable diagnosis fields cannot select history. Changing scope remounts the view and aborts the old request. Missing evidence, empty, unavailable, forbidden, stale, loading and network states have distinct messages.

## D. Files for review

| Member 6 files | Purpose |
|---|---|
| New backend/app/services/repair/graph_policy.py | Typed grant and plan, graph fingerprint, topology checks and isolated application |
| New backend/app/services/repair/history.py | Authorized scoped read protocol and redacted projection |
| New backend/app/services/repair/structural.py | In-process bridge to the published Member 5 validator |
| Modified backend/app/services/repair/diagnosis.py | Exact structural codes and trusted connection reference |
| Modified backend/app/services/repair/recovery_contracts.py | Graph operation references and shared attempt presentation schema |
| Modified backend/app/services/repair/recovery_graph.py | Graph restoration and independent structural gate in the existing graph |
| Modified backend/app/services/repair/integration.py | Optional graph, structural and history bindings, authorization and pagination |
| Modified backend/app/api/v1/endpoints/repair.py | Scoped history route with bounded query parameters |
| Modified backend/examples/member6_demo.py | Graph restoration, human review and history scenarios |
| New backend/tests/test_repair_graph_history.py | Eligibility, isolation, verification, history and denial regressions |
| New backend/tests/repair_history_browser_fixture.py | Synthetic scoped reader of disposable disk-backed fixture records for Chrome |
| New frontend/src/components/activity/RepairHistory.tsx | Scoped history and attempt details |
| New frontend/src/components/activity/repairHistoryApi.ts | Bounded fetch, scope verification, status and error handling |
| Modified frontend/src/components/activity/RepairPanel.tsx | Selection handoff and history placement |
| Modified frontend/src/components/activity/repairApi.ts | Require execution run identity for verified-candidate display |
| New frontend/tests/repairHistory.test.mjs | History transport, invalid result and outcome presentation tests |
| New frontend/tests/repairHistoryBrowser.mjs | Chrome interaction with actual React view and FastAPI fixture reader |
| Modified docs/MEMBER6_IMPLEMENTATION.md and docs/REPAIR_RECOVERY_GRAPH.md | Updated contracts, flow, demo and results |
| New docs/MEMBER6_COMPLETION.md | Current review evidence and submission conditions |

Shared coordination centers on the Member 4 monitor selection, Member 3 graph policy and Member 1 read authorization. The work does not edit their source or shared workflow schema.

## E. Verification

From backend/ with the existing Python 3.11 virtual environment, PowerShell:

```powershell
$env:DATABASE_URL="sqlite:///$env:TEMP/member6-$([guid]::NewGuid()).db"
$env:DEBUG='false'
./.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider --tb=short
./.venv/Scripts/python.exe -B -m examples.member6_demo
```

Published baseline **255 passed**, final **305 passed** (50 additions, zero failed or skipped). An initial plain in-memory SQLite run failed in workflow CRUD because worker threads saw separate databases. A fresh disposable SQLite file resolved this without a change to existing tests. Demo outcomes include scalar, edge and mapping promotion, credentials and missing policy human review, regression rejection with confirmed rollback, stale revision, absent dependencies and scoped history. The compiled LangGraph is real. Its lifecycle and verifier in the demo are fixtures.

From frontend/:

```powershell
node --experimental-strip-types --test tests/repairApi.test.mjs tests/repairHistory.test.mjs
npm run build
node tests/repairHistoryBrowser.mjs
```

Baseline 4 frontend tests. Final **10 passed**, zero failed or skipped. TypeScript and production Vite build passed. A case-insensitive filename collision found by TypeScript during development was corrected. Vite reported the existing large chunk and compiler-directive warnings. Chrome used a disposable profile, a loopback Vite host, and the actual FastAPI history route with a test-only session and on-disk records. Confirmed promotion, reload/refetch, workflow switch with delayed prior response, regression failure and confirmed rollback were observed. This verifies presentation across a browser reload. It does not exercise Member 1 storage or authorization.

Startup TestClient probes returned 200 on /api/v1/health and /api/v1/repair/readiness, and 503 on unconfigured diagnose, recover and history. The optional isolated package set previously installed under the audit temp directory imported google-genai 1.75.0 and LangGraph 1.2.24. With that package overlay on PYTHONPATH, `./.venv/Scripts/python.exe -B -m pip check` reported no broken requirements. Gemini uses a configurable server model and key, timeout and one SDK attempt, structured advisory-only schema and allowlisted observations. Mock transport covers rejected requests, errors and measured/unknown usage. Live verification is outstanding. The default smoke command exited without a network request. After explicit authorization, the command from backend/ is `python -m examples.member6_gemini_smoke --live`.

For the isolated cross-branch probe, Member 5's published schema and validation package were loaded from the 3c7800d audit archive. Member5StructuralValidation(WorkflowValidator()).check(snapshot) passed a two-node public graph with output → input and failed the same graph with an invalid source handle. This crosses the real Python interface. Full production composition for promotion, regression failure, rollback, duplicate recovery and concurrent edits is blocked. Equivalent contract scenarios run with fixtures.

## F–G. Production inventory and acceptance contracts

The refreshed refs are main 2130384, Member 1 1bbbe07, Member 2 fe24f81, Member 3 8970f83, Member 4 e97da64, Member 5 3c7800d and Member 6 66a7be6. The unchanged Member 2 development worktree is outside this review.

Every row below is **unconfigured in the production host**. The optional structural bridge is verified in isolation. Method-level inputs and outputs for every original binding are also in [the team handoff](MEMBER6_IMPLEMENTATION.md).

| Readiness binding | Owner | Published capability | Needed for acceptance |
|---|---|---|---|
| authorization | 1 | Optional global API key | RepairAccess.allows(request, scope, action) must verify a host-authenticated principal and deny cross-tenant, unauthorized action, or mismatched run access. Add history permission. |
| failure_evidence | 4 | get_failure_evidence returns a record and redacted logs, with mutable fallback | get_failure(scope) must return an exact immutable failed run, stable error code, node and approved context. Supply the connection ID for graph repair. Reject success, missing snapshot and mismatched revision. |
| snapshot | 1 | Mutable CRUD rows | save_snapshot(workflow, revision) must return immutable exact graph bytes or conflict for a stale revision. |
| schema_policy | 3 | Canonical nodes, edge IDs and handles | Supply approved scalar fields and GraphAuthority.permit(failure, edge_id), with exact schema, purpose, type, protected-path and graph digest checks. |
| replacement | 1 + 3 | No authenticated working revision store | get_replacement(target) or working_snapshot(permit) must return authorized known-working state for the same workflow and policy. |
| original_requirements | 2 | Acceptance criteria in generated plan | get_original_requirements(workflow, revision) must resolve an immutable original baseline including restrictions and stable criteria IDs. |
| attempt_reservation | 1 | Caller-editable counters | begin(scope), reserve(scope, number, limit=2), finish(scope, result) must enforce uniqueness and count transactionally across workers and restarts. |
| candidate_execution | 4 | execute_isolated_candidate returns execution report | Return server-issued run and exact immutable candidate revision association, with safe isolation, inputs and principal. Preserve approvals. |
| structural_validation | 5 | Real WorkflowValidator.validate(nodes, edges, workflow_id) | Host can inject Member5StructuralValidation(WorkflowValidator()) using RepairBindings.structural when both modules are installed. Verify exact snapshot, identity, counts and consistent verdict; a valid structure alone cannot promote. |
| regression_verification | 5 + 4 | Scenarios and caller-supplied comparison | get_baseline(scope) and verify(candidate, baseline) must fetch immutable definitions, execute failed and previously passing tests, and return bound actual outcomes. |
| revision_lifecycle | 1 | No transactional promote/restore interface | find_last_working_snapshot(workflow), promote_candidate(candidate, expected_revision_id) and restore_snapshot(snapshot, expected_revision_id) must use compare-and-swap and return confirmed, failed or conflict after commit. |
| repair_recording | 1 | Execution records, no durable recovery ledger | record_attempt(original, run, attempt) and record_outcome(result) must store redacted, idempotent records. HistorySource.read(request, scope, offset, limit) returns HistoryPage or None after authorization. Commit recovery IDs, timestamps and retention. |

Frontend handoff from Member 4 requires a selected failed execution with all three server-issued identifiers. The UI accepts this through RepairPanel.failedExecution. Member 1's service must independently authorize and match the selection. Membership of a branch or a successful API response does not establish a verified repair.

## H–J. Security, Git and decision

Graph application has no generic patch interpreter, provider-supplied values, arbitrary tool execution, or generic config mutation. The public API receives scope identifiers only for recovery. The reader rejects mismatched records and inconsistent terminal proof. The default host stays fail-closed. Deployment still depends on trusted host code supplying correct grants, records and transactional confirmations. Offset-based history lists can shift while new entries are being appended. Live provider connectivity is unverified. The changed-file credential-pattern scan found zero matches and no environment, database, cache or log artifacts. Git confirmed the root .env is ignored and untracked. The whitespace check passed for tracked changes and new files.

Release candidate is local on feature/member6-self-repair at 66a7be6. Proposed commits:

1. `feat(repair): restore verified connections and port mappings`
2. `feat(repair): present scoped recovery history with verification evidence`
3. `docs(repair): record validation evidence and production handoff`

Ready for independent review of the bounded implementation. Final merge and production activation remain pending. The remaining Member 6 work is wiring the real selection and owner services, then rerunning production composition and the authorized provider smoke. No commit, push, merge or pull request was performed.
