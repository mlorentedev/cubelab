---
spec: "TOOL-036-platform-manifest-sync"
verdict: "PASS-WITH-GAPS"
reviewed_sha: "924eb47c64c12bbab328a0d5256d2a61408ff30e"
reviewer: "agy/gemini-3.1-pro-high"
date: "2026-09-06"
---

## Adversarial review

**Scope**: TOOL-036-platform-manifest-sync
**Sources**: `specs/TOOL-036-platform-manifest-sync/{proposal,tasks,verification}.md`, `features.json`, diff `56736475...HEAD` (14 commits), `web` repository (`site/src/data/platform.ts`, `site/src/components/LabProvenance.astro`, `site/tests/lab-*.test.mjs`)

### Spec and task alignment

- **Acceptance Criteria AC1–AC5 verified through direct execution:**
  - **AC1 (Schema projection from SSOT):** `poetry run pytest tests/test_sync_platform_json.py -k test_manifest_schema_and_counts` passes. Projected JSON conforms to `site/src/data/platform.ts` interface shapes, field names, and enums (`k3s`, `docker`, `systemd`, `standby`, `healthy`, `warning`, `offline`).
  - **AC2 (Zero-Addressing isolation):** Verified by `test_zero_addressing_sanitization`, `test_zero_addressing_guard_catches_leaked_ip`, `test_zero_addressing_guard_catches_leaked_ipv6`, `test_zero_addressing_guard_catches_internal_hostname`, and `test_zero_addressing_guard_does_not_falsely_catch_mac_address`. The fail-closed regex gates in `generate_manifest` catch IPv4, IPv6 (`fd7a:...`, `::1`), and `.internal`/`.local`/`.lan` domains while allowing hardware MAC addresses (`00:11:22:33:44:55`), timestamps, and semver strings.
  - **AC3 (Drift gating):** `make sync-platform-json-check` exits 0. `test_drift_gate_detects_mutation` and `test_drift_gate_across_simulated_commit_boundary` verify that changes in `common.yaml` trigger non-zero exit with unified diff output, while unchanged content preserves `generated_at` across checks.
  - **AC4 (Makefile targets):** `make sync-platform-json-check` and `make validate-sync` executed directly in this session and return exit 0.
  - **AC5 (Testing & safety boundary):** 22 tests in `tests/test_sync_platform_json.py` pass; branch/line coverage of `toolkit/features/platform_manifest.py` is measured at **100%** (197 statements, 80 branches, 0 missed). Static checks (`mypy toolkit/features/platform_manifest.py`, `ruff check`, `radon cc`) pass with max Cyclomatic Complexity of 14 (below the 15 threshold).
- **Stale CI comment resolved:** The previous finding regarding `.github/workflows/check-config-drift.yml` citing non-existent `_get_commit_provenance` has been resolved in commit `46377aeb`, and `fetch-depth` is cleanly set to 1.
- **Contract files unchanged:** `proposal.md`, `tasks.md`, and `features.json` were not altered during this review. No live `[AGENT-DRAFT]` or `[AGENT-SUGGESTION]` markers remain.

### Findings

| Severity | Reality | Area | Finding | Evidence | Test (named, or UNTESTED) | Fix location (code / tests / spec / vault) |
|----------|---------|------|---------|----------|---------------------------|---------------------------------------------|
| Major | THEORETICAL | Cross-boundary integration (provenance semantics) | Producer emits `source_commit` as a git blob SHA-1 of `common.yaml`, but `web`'s consumer in `site/src/components/LabProvenance.astro:27` constructs `https://github.com/mlorentedev/web/commit/${platform.source_commit}`. A blob hash is not a commit, and `common.yaml` resides in `kubelab`, not `web`. Clicking the rendered link on `mlorente.dev/lab` will return a 404 once `web` consumes this manifest. Currently latent because `web` still ships a static hand-written manifest. `web`'s unit tests assert only `/^[0-9a-f]{7,40}$/`, masking the breakage. | Code read of `web/site/src/components/LabProvenance.astro:25-27` vs `platform_manifest.py:593-601` (`compute_source_hash`). | UNTESTED (`kubelab` does not test downstream `web` UI links) | spec (document downstream requirement) + `web` repo (`LabProvenance.astro`) |
| Minor | REAL | Maintainability (magic numbers) | `compute_total_services` returns `len(stg) + len(prd) + 2` with an undocumented magic `+2` offset to force the total to 35 (16 staging + 17 prod + 2). | Code read of `platform_manifest.py:842`; `build_service_tables(config)` yields 16 and 17. | `test_compute_total_services_calculation` | code (document or name constant) |
| Minor | REAL | Type consistency (mypy test coverage) | Four test functions (`test_zero_addressing_guard_catches_leaked_ip`, `…_ipv6`, `…_internal_hostname`, `…_does_not_falsely_catch_mac_address`) leave `monkeypatch` untyped, failing `mypy` with `no-untyped-def` when run directly on `tests/`. CI currently only checks `mypy toolkit`, masking the untyped fixtures. | `poetry run mypy tests/test_sync_platform_json.py` fails with 4 `no-untyped-def` errors; `mypy toolkit` passes cleanly. | mypy | tests (annotate `monkeypatch: pytest.MonkeyPatch`) |
| Minor | THEORETICAL | Dynamic service discovery scope | `project_services` iterates over static `SERVICE_CATALOG_DEFAULTS` (14 services). Any new service added under `apps.services` in `common.yaml` that is absent from `SERVICE_CATALOG_DEFAULTS` is omitted from `platform.json`. | Code read of `project_services` / `_collect_ssot_services`; `test_dynamic_public_service_from_ssot` requires monkeypatching `SERVICE_CATALOG_DEFAULTS`. | `test_dynamic_public_service_from_ssot` | code / spec |
| Minor | THEORETICAL | Error UX | Zero-addressing leak raises `ValueError` in `generate_manifest`, propagating an unhandled traceback through `sync()`. The tool fails closed (exit non-zero, nothing written), so safety is preserved, but error reporting is unhandled. | Code read of `sync()` in `platform_manifest.py:930`. | `test_zero_addressing_guard_catches_leaked_ip` | code (catch `ValueError` and log clean error message) |

### Evaluator rubric

| Dimension | Grade (A-D) | Rationale (one line) |
|-----------|-------------|----------------------|
| Correctness        | B | AC1–AC5 verified; output strictly enforces zero-addressing; the only correctness gap is downstream `source_commit` link semantics in `web`. |
| Verification       | A | Reproducible evidence executed directly: 22 tests pass with 100% line/branch coverage, `make sync-platform-json-check` and `make validate-sync` exit 0, max CC is 14. |
| Scope              | B | Diff matches proposal requirements; subsequent commits on branch addressed Windows CI drift reporting and merged upstream `master`. |
| Reliability        | A | Robust fail-closed behavior on data leakage; idempotent timestamp preservation on clean checks; graceful handling of corrupt/non-mapping configs. |
| Maintainability    | B | Max CC 14 (below 15); cleanly structured and typed implementation; minor smell with undocumented `+2` offset and untyped test parameters. |
| Handoff-readiness  | B | Tasks and verification reflect design decisions; downstream `web` link dependency documented as a carried gap. |

### Verdict
PASS WITH GAPS

No Blockers. One Major finding (cross-boundary `source_commit` URL semantics in `web`), which is classified as THEORETICAL because `web` currently still serves its own hand-written manifest and the fix belongs in the `web` repository. All evaluator rubric dimensions grade B or above.

### Recommended next steps

1. **Downstream `web` PR (Issue `web#162` / `WEB-073`):** Update `site/src/components/LabProvenance.astro` in the `web` repository to link `source_commit` to `https://github.com/mlorentedev/kubelab/blob/master/infra/config/values/common.yaml` (or remove the anchor link), matching the fact that `source_commit` is a git blob SHA-1 of `kubelab`'s `common.yaml`.
2. **Type annotations in test suite:** Annotate the `monkeypatch` parameter in `tests/test_sync_platform_json.py` as `pytest.MonkeyPatch` to satisfy strict typing under `disallow_untyped_defs = true`.
3. **Document or name constant:** Clarify the rationale for the `+2` workload offset in `compute_total_services` within `toolkit/features/platform_manifest.py`.
