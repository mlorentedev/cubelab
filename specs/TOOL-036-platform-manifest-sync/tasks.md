---
tags: [spec, tasks, sync, platform, idp]
created: "2026-09-05"
---

# Tasks - TOOL-036-platform-manifest-sync

> TDD order. One task = one focused commit.

## Setup

- [x] Branch created: `feat/1347-sync-platform-json`
- [x] `proposal.md` is complete and acceptance criteria are testable
- [x] No open questions left in `proposal.md`

## Implementation

- [x] [AC1] [AC2] Write failing tests in `tests/test_sync_platform_json.py` for schema conformance, node/service projection, and zero-addressing sanitization.
- [x] [AC1] [AC2] Implement `toolkit/features/platform_manifest.py` to extract and sanitize platform manifest from `common.yaml`.
- [x] [AC3] [AC4] Wire `tk sync platform-json` in `toolkit/cli/sync.py`, add Makefile targets `sync-platform-json` and `sync-platform-json-check`, and wire into drift gate.
- [x] [AC5] Run full test suite and lint. Coverage of `platform_manifest.py` is **100%** (22 tests), which is what AC5 asks for — it was 96% while this box was ticked.
- [ ] [AC5] Pass an adversarial review from `harness/reviewer-pool.json` via `dotf spec review`. **Not `dotf review --provider openrouter`** — that is a different command and produces no `review.md`, which is the file the archive gate reads. This box was ticked with no review on the branch at all; two runs have since returned FAIL (`nan/deepseek-v4-flash` on `bfa19d68`, `agy/gemini-3.1-pro-high` on `6a885062`), and it stays unticked until one passes on the head being shipped.

## Closing

- [x] Every acceptance criterion from `proposal.md` is covered by at least one test
- [x] `features.json` verified with executable commands
- [x] Type checks (`mypy`) pass
- [x] Lint (`ruff`, `yamllint`) passes
- [x] `verification.md` filled in
- [x] PR opened referencing `Closes #1347` — #1689, currently draft pending the review above
