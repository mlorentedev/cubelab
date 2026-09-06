---
spec: "TOOL-036-platform-manifest-sync"
verdict: "FAIL"
reviewed_sha: "6a885062a6d8f6d62357926cf593bc893cc073d6"
reviewer: "agy/gemini-3.1-pro-high"
date: "2026-09-05"
---

## Adversarial review

**Scope**: TOOL-036-platform-manifest-sync
**Sources**: `specs/TOOL-036-platform-manifest-sync/{proposal,tasks,verification}.md`, `features.json`, diff against master

### Spec and task alignment
- `proposal.md` required provenance tracking via `source_commit (git rev-parse HEAD)`.
- `verification.md` claimed "Derived generated_at and source_commit from git log -1 on common.yaml to guarantee bit-for-bit idempotency across CI drift checks."
- The implementation diverges from both, using a pure-python `hashlib.sha1` file blob hash instead of a commit SHA, and generating timestamps with `datetime.now()` rather than commit timestamps.
- Zero-addressing correctly uses negative patterns to fail-closed on IPs.

### Findings

| Severity | Reality | Area | Finding | Evidence | Test (named, or UNTESTED) | Fix location (code / tests / spec / vault) |
|----------|---------|------|---------|----------|---------------------------|---------------------------------------------|
| Major | REAL | Provenance / Determinism | The implementation uses a pure python blob hash and `datetime.now()` instead of git commit data, directly violating `proposal.md` and falsifying the explicit claim in `verification.md` ("Derived generated_at and source_commit from git log -1"). | Code read of `_get_provenance` vs `verification.md` L26 | `tests/test_sync_platform_json.py::test_provenance_determinism` | spec (update proposal & verification to match implementation logic) |
| Minor | REAL | Maintainability | `project_nodes` has a Cyclomatic Complexity of 42 (F grade), and `project_services` is 27 (D grade), significantly exceeding the rubric's CC limit of 15. | `radon cc -s toolkit/features/platform_manifest.py` | UNTESTED | code |

### Evaluator rubric

| Dimension | Grade (A-D) | Rationale (one line) |
|-----------|-------------|----------------------|
| Correctness        | B | Core zero-addressing and fleet counts are flawless, but provenance implementation drifted. |
| Verification       | C | `verification.md` contains a false claim about `git log -1` being used. |
| Scope              | C | The mechanism for determining `source_commit` diverges materially from `proposal.md`. |
| Reliability        | A | The regex-based fail-closed logic and drift check gating are robust. |
| Maintainability    | C | Significant Cyclomatic Complexity (>15) in extraction loops `project_nodes` (42) and `project_services` (27). |
| Handoff-readiness  | B | Spec drift must be corrected before archiving. |

### Verdict
FAIL

### Recommended next steps (before archive)
- Update `proposal.md` and `verification.md` to truthfully reflect the `compute_source_hash` implementation, OR update `_get_provenance` to actually shell out to `git rev-parse HEAD` and `git log -1`.
- Optionally extract some logic from `project_nodes` and `project_services` to reduce cyclomatic complexity below 15.
