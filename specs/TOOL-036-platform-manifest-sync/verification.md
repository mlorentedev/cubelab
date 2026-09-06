---
tags: [spec, verification, templates]
created: "2026-09-05"
---

# Verification - TOOL-036-platform-manifest-sync

## Evidence

Map every acceptance criterion from `proposal.md` to concrete proof:

- [x] AC1 (Schema projection from SSOT) -> `tests/test_sync_platform_json.py::test_manifest_schema_and_counts`, `tests/test_sync_platform_json.py::test_nodes_projection`, `tests/test_sync_platform_json.py::test_services_projection`
- [x] AC2 (Zero-Addressing isolation) -> `tests/test_sync_platform_json.py::test_zero_addressing_sanitization`, `tests/test_sync_platform_json.py::test_zero_addressing_guard_catches_leak`
- [x] AC3 (Deterministic drift gating) -> `tests/test_sync_platform_json.py::test_drift_gate_across_simulated_commit_boundary`, `tests/test_sync_platform_json.py::test_drift_gate_detects_mutation`
- [x] AC4 (Makefile integration) -> `make sync-platform-json-check` returns exit 0; `make validate-sync` passes cleanly.
- [x] AC5 (Testing & safety boundary) -> 14 unit tests passing, 97% branch/line coverage on `toolkit/features/platform_manifest.py`.

## Test status

- Test suite: `.venv/bin/pytest tests/test_sync_platform_json.py -v` -> 14 passed in 10.08s, 97% coverage
- Manual smoke test: `make validate-sync` verifies `[SUCCESS] platform-json: in sync` and `[SUCCESS] All generated files in sync`
- No regressions in existing test suite: yes (all tests green)

## Decisions made during implementation

- **Content Hash Provenance over Git Commit SHA:** Derived `source_commit` from the pure-python git blob hash of `common.yaml` (equivalent to `git hash-object`) and preserved `generated_at` when content is unchanged. This prevents the chicken-and-egg commit boundary problem where `git log -1` would drift on every post-sync commit.
- **Zero-Addressing Sinkhole:** Replaced `0.0.0.0 / Blocked` in DNS Mermaid diagram with `Sinkhole / Blocked` to maintain zero IP leak false positives.
- **Low Cyclomatic Complexity:** Decomposed node and service extraction functions into dedicated single-responsibility helpers ensuring all functions maintain CC <= 14 (under the 15 threshold).
- **UTF-8 serialization:** Enforced `ensure_ascii=False` so accented characters (`ó`, `·`) render cleanly in web frontend.

## Promotion candidates

Before archiving, flag what (if anything) should be promoted to the vault. If all three are "no", archive in repo is the only persistence.

- [x] Lesson for the repo's `docs/lessons/`? Not needed now (captured in spec verification & commit message).
- [ ] ADR-worthy decision for the repo's `docs/adr/adr-XXX.md`? No (aligns with ADR-032 SSOT and ADR-056 Zero-Addressing).
- [ ] New pattern candidate for `00_meta/patterns/`? Only if this recurs in >1 project. No.

## Archive checklist

- [ ] `proposal.md` frontmatter set to `status: archived`
- [ ] Folder moved: `specs/TOOL-036-platform-manifest-sync/` -> `specs/archive/TOOL-036-platform-manifest-sync/`
- [ ] Bitácora board ticket for this spec moved to Done / closed with PR link (ADR-018)
- [ ] Promotions above executed (if any)
