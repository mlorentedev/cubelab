---
tags: [spec, verification, templates]
created: "2026-09-05"
---

# Verification - TOOL-036-platform-manifest-sync

## Evidence

Map every acceptance criterion from `proposal.md` to concrete proof:

> Test names below are copied from the file, not written from memory. Three of the
> names this section used to carry — `test_nodes_projection`,
> `test_services_projection`, `test_zero_addressing_guard_catches_leak` — never
> existed. Evidence that names a test nobody can run is indistinguishable from no
> evidence, and it reads stronger than a blank.

- [x] AC1 (Schema projection from SSOT) -> `test_manifest_schema_and_counts`, `test_dynamic_projection_from_mock_config` (mutates the mock SSOT and asserts the output follows), `test_dynamic_public_service_from_ssot`, `test_compute_total_services_calculation`
- [x] AC2 (Zero-Addressing isolation) -> `test_zero_addressing_sanitization`, `test_zero_addressing_guard_catches_leaked_ip`, `test_zero_addressing_guard_catches_leaked_ipv6`, `test_zero_addressing_guard_catches_internal_hostname`, `test_zero_addressing_guard_does_not_falsely_catch_mac_address`
- [x] AC3 (Deterministic drift gating) -> `test_drift_gate_across_simulated_commit_boundary`, `test_drift_gate_detects_mutation`, `test_drift_gate_missing_file_returns_error`, `test_provenance_determinism`, `test_provenance_content_hash`
- [x] AC4 (Makefile integration) -> `make sync-platform-json-check` returns exit 0; `make validate-sync` passes cleanly.
- [x] AC5 (Testing & safety boundary) -> 22 unit tests passing, **100%** branch/line coverage on `toolkit/features/platform_manifest.py`, which is what AC5 asks for. It was 97% while this line claimed 97% and the criterion said 100%; the gap was closed by covering the five real defensive paths that had none (corrupt existing manifest, `warning` node status, the `edge.traefik` fallback, non-mapping entries in the services tree, and an already-prefixed K3s version) rather than by rewording the criterion.

## Test status

- Test suite: `poetry run pytest tests/test_sync_platform_json.py` -> 22 passed, 100% coverage
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
