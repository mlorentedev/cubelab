---
spec: "TOOL-036-platform-manifest-sync"
verdict: "PASS-WITH-GAPS"
reviewed_sha: "521f5cc3c9f423149413654af2258d539ddeb9b2"
reviewer: "nan/deepseek-v4-flash"
date: "2026-09-05"
---

## Adversarial review

**Scope**: TOOL-036-platform-manifest-sync
**Sources**: `specs/TOOL-036-platform-manifest-sync/{proposal,tasks,verification}.md`, `features.json`, diff `56736475...HEAD` (9 commits), `web` repo (`site/src/data/platform.ts`, `site/src/components/LabProvenance.astro`, `site/tests/lab-*.test.mjs`)

### Spec and task alignment

- **AC1–AC5 all satisfied.** Verified end-to-end, not by reading assertions:
  - `pytest tests/test_sync_platform_json.py` → **22 passed**, `platform_manifest.py` **100%** line/branch coverage (197 stmts / 80 branches, 0 missed). AC5's "100% unit test coverage with negative controls" holds.
  - Zero-addressing (AC2): generated manifest contains **no** IPv4, IPv6, `.internal/.local/.lan` hostnames, or `100.64.`/`172.16.` subnets. Regexes verified against MAC (`00:11:22:33:44:55` correctly NOT caught), real IPv6 forms (caught), timestamp `2026-09-05T20:31:19Z` and semver `v1.34.4+k3s1` (correctly NOT caught).
  - Drift gate (AC3): `make sync-platform-json-check` exits 0; `make validate-sync` exits 0; committed `infra/config/platform.json` `source_commit` == `compute_source_hash(common.yaml)` (both `8411e251…`).
  - Makefile (AC4): `sync-platform-json` / `sync-platform-json-check` targets wired; `make validate-sync` green.
- **Previous round's two findings are resolved.**
  - *Major (REAL)* "provenance diverges from proposal": the implementer edited `proposal.md` (commit `71caa0d1`) to specify `source_commit` = "deterministic git blob SHA-1 hash of `common.yaml`". Spec, `verification.md` "Decisions", and `compute_source_hash` now agree. The content-hash choice is defensible (it solves the chicken-and-egg `git log -1` drift the proposal now documents); acceptance criteria are mechanism-agnostic. This is a spec-alignment change, not a goalpost move that hides a defect.
  - *Minor (REAL)* "CC 42/27": decomposed in `71caa0d1`; `radon cc -s` now reports **max CC = 14** (`_collect_ssot_services`, `_discover_fleet_nodes`), all under the 15 threshold.
- `[AGENT-DRAFT]` / `[AGENT-SUGGESTION]` tags: **none** in `proposal.md`, `tasks.md`, `features.json`, `verification.md`.
- Contract files (`proposal.md`, `tasks.md`, `features.json`) were **not** modified during this review.

### Findings

| Severity | Reality | Area | Finding | Evidence | Test (named, or UNTESTED) | Fix location (code / tests / spec / vault) |
|----------|---------|------|---------|----------|---------------------------|---------------------------------------------|
| Major | THEORETICAL | Cross-boundary (provenance semantics) | The producer emits `source_commit` as a **blob SHA-1 of `kubelab`'s `common.yaml`**, but `web`'s consumer treats it as a **commit SHA in the `web` repo** and builds a clickable link. `web/site/src/components/LabProvenance.astro:27` does `commitUrl = "https://github.com/mlorentedev/web/commit/" + platform.source_commit`. When `web` adopts the produced manifest, that URL 404s (the blob hash is neither a commit nor in the `web` repo). The proposal's risk resolution ("pin field names/enum values to match `platform.ts`") covers type assertions but not this semantic use. Not currently triggered: `web` ships its own hand-written `platform.json` (`source_commit: df583dbf…`, a `web` commit), and the producer output lives separately in `kubelab`. | Read `web/site/src/components/LabProvenance.astro:25-27` vs `platform_manifest.compute_source_hash` (blob hash). `web`'s `lab-data.test.mjs` only asserts `/^[0-9a-f]{7,40}$/`, which a blob hash satisfies — so `web`'s tests stay green while the rendered link silently breaks. | UNTESTED (no test in `kubelab` exercises `web`'s consumption) | spec (document the required downstream `web` change) + `web` repo (out of scope here) |
| Minor | REAL | CI config comment | `.github/workflows/check-config-drift.yml` comment claims provenance is derived from `git log -1 -- common.yaml` via `_get_commit_provenance`, but that function does not exist and the implementation uses `compute_source_hash`. `fetch-depth: 0` is now unnecessary (a content hash reads no git history); it is harmless but the justification is false. | `grep -rn "_get_commit_provenance\|git log -1"` matches only the comment in `check-config-drift.yml`; no such symbol in `toolkit/`. | UNTESTED (comment; not testable) | code (update/remove the stale comment in the workflow; optionally revert `fetch-depth`) |
| Minor | REAL | Maintainability | `compute_total_services` returns `len(stg) + len(prd) + 2` with an undocumented magic `+2` (35 for the current config = 16+17+2). The `+2` is a silent fudge with no named meaning. | Code read of `compute_total_services`; `build_service_tables` → stg=16, prd=17. | `test_compute_total_services_calculation` (hardcodes 35; brittle) | code (name/document the constant) |
| Minor | REAL | Type consistency | Four test functions (`test_zero_addressing_guard_catches_leaked_ip`, `…_ipv6`, `…_internal_hostname`, `…_does_not_falsely_catch_mac_address`) leave the `monkeypatch` parameter untyped, violating `disallow_untyped_defs=true`. The repo gate `mypy toolkit` does not scan `tests/`, so this is not caught by CI. | `mypy tests/test_sync_platform_json.py` → 4 `no-untyped-def` errors; `mypy toolkit` → clean. | mypy | tests (annotate `monkeypatch`) |
| Minor | THEORETICAL | Dynamic projection scope | `project_services` iterates over the **static** `SERVICE_CATALOG_DEFAULTS` (14 services). A service declared in SSOT but absent from the catalog is silently **omitted** from the manifest (not leaked — just missing). "Dynamic" covers field overrides only, not service discovery. | Code read of `project_services` / `_collect_ssot_services`; `test_dynamic_public_service_from_ssot` monkeypatches the catalog to add a service. | `test_dynamic_projection_from_mock_config` | spec (clarify discovery scope) / code |
| Minor | THEORETICAL | Error UX | A zero-addressing violation raises `ValueError` in `generate_manifest`, which propagates uncaught through `sync()` so the CLI prints a traceback. It still fails closed (non-zero exit, nothing written), so not a safety hole — just an ugly failure. | Code read of `sync()` / `generate_manifest`. | `test_zero_addressing_guard_catches_leaked_ip` (asserts the raise, not the CLI UX) | code (catch and report cleanly) |

### Evaluator rubric

| Dimension | Grade (A-D) | Rationale (one line) |
|-----------|-------------|----------------------|
| Correctness        | B | All five acceptance criteria verified; output is deterministic, leak-free, and enum-conformant to `platform.ts`; the only correctness gap is the downstream `source_commit` semantic mismatch (THEORETICAL). |
| Verification       | A | Evidence is reproducible — I re-ran the full suite (22 passed, 100% cov), `make sync-platform-json-check`, `make validate-sync`, `mypy toolkit`, `ruff`, `radon cc` — and it holds. |
| Scope              | B | Diff matches the proposal; the `fetch-depth: 0` CI side-change is now stale/inconsistent (Minor above). |
| Reliability        | A | Error paths handled (missing config, invalid YAML, corrupt manifest, missing file, fail-closed zero-addressing); drift gate idempotent (preserves `generated_at`); `_run_with_check` restores snapshots. |
| Maintainability    | B | Max CC 14 (under 15); minor smells: magic `+2`, 4 untyped test params, `source_commit` misnomer. |
| Handoff-readiness  | B | Spec and verification updated to the content-hash decision; the required downstream `web` change (LabProvenance.astro link) is not captured as a handoff item. |

### Verdict
PASS WITH GAPS

One open **Major (THEORETICAL)** — the cross-boundary `source_commit` semantics — is tracked below; it is THEORETICAL (not yet triggered; `web` still ships its own hand-written manifest) and its fix is downstream in `web` plus spec documentation, so it does not force FAIL. All rubric dimensions are B or above; no Blocker, no REAL Major.

### Recommended next steps (before archive)

1. **Document the downstream `web` dependency in `proposal.md`** (or a follow-up issue): when `web` adopts the produced manifest, `LabProvenance.astro` must stop hardcoding `https://github.com/mlorentedev/web/commit/${source_commit}` (point at the `kubelab` repo, or drop the link), because `source_commit` is a `kubelab` blob hash, not a `web` commit. This is the gap the "pin field names" resolution does not cover.
2. **Fix the stale CI comment** in `.github/workflows/check-config-drift.yml` — it references `_get_commit_provenance` and `git log -1`, which no longer exist; `fetch-depth: 0` is no longer required by the content-hash provenance.
3. **Name or document the `+2`** in `compute_total_services`, and annotate the four `monkeypatch` test parameters (type consistency under `disallow_untyped_defs`).
4. Confirm with the author whether `web`'s `LabProvenance.astro` will be updated in the downstream `web` PR (finding 1 is otherwise an open integration risk).

`dotf spec archive` / `/spec archive` is **advisable** once the above are dispositioned; the current `review.md` is fresh (HEAD `521f5cc3`) and on a pool-member model, but the stale CI comment and the `source_commit` downstream note should be tracked before archiving so they are not lost.
