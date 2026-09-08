# KubeLab multi-angle audit — 2026-09-07

Whole-repo audit from six angles: development (code quality), infrastructure
best practices, UI/UX/SEO, content and documentation, process and backlog
hygiene, and a reconciliation of the three July 2026 audits in this directory.
Every finding is traced to `file:line`, marked CONFIRMED (path followed end to
end) or PLAUSIBLE, and cross-referenced against the 508 open issues, the 21
active specs, the four remote branches, the three worktrees, and the project's
knowledge-store entries.

> **Method.** Six parallel read-only passes, each with the same contract: the
> open-issue dump, the July audit IDs, and one cross-reference tag per finding
> from {NEW, COVERED #N, PARTIAL #N, STILL-OPEN-SINCE-JULY id}. The first wave
> died on a session limit after one pass completed; the second wave reused the
> first wave's intermediate artefacts (rendered overlays, issue dump, CI runs).
> GitHub GraphQL was rate-limited for the whole session, so the bitácora board
> itself was not read; every board-derived statement is inferred from labels
> and titles. The top findings were re-verified by hand before publication.
>
> **Scope note on UI/UX/SEO.** The web app left this repo (ADR-053) and the blog
> was killed, so those angles cover what remains here: the error pages, the
> Homepage cockpit, the one Grafana dashboard, the GitHub repository presence,
> the public exposure inventory, and the CLI surface. The extracted web repo was
> not audited.

---

## 1. Headline

The July audits fixed the outer ring and left the deep reference material
alone, and two months of migrations have added a new outer-ring drift on top:
the three documents every agent is told to read first (README, AGENTS.md,
CLAUDE.md) all place the Argo CD hub on AWS, fifteen days after `aws1` was
destroyed. Underneath that, the code and IaC surfaces the July audit admitted it
never reached turned out to hold the highest-severity new findings: the toolkit
CLI prints plaintext secrets by default, the Go API health check cannot fail, a
tested fix for a silent secret omission has sat unmerged on a stale branch for
thirteen days, and seventeen of eighteen workloads run with no pod security
context. Process hygiene is the third theme: six ticket-ID collisions, three
specs still active for shipped work, and a backlog whose "zero stale issues"
is an artefact of a single-day import.

Counts: **58 findings in the summary table** (1 critical, 16 high, 23 medium,
16 low, 2 informational; 33 of them new, the rest July findings re-confirmed
and re-severitised), plus the July reconciliation: **123 July findings
re-checked, 47 fixed, 4 partial, 71 still true, 1 obsolete**.

This audit is the second pass that #834 (OPS-013, "second-pass audit of
uncovered areas") asked for: Ansible roles, the Kustomize tree, Terraform, the
pytest suite and the Go API were exactly the areas the July codebase audit
declared shallow, and they are where this pass found its highest-severity new
items.

---

## 2. Summary table

Severity order within each angle. IDs are stable; a fixing agent should cite
them. Cross-ref: NEW (no ticket), COVERED #N (ticket exists, nothing to add),
PARTIAL #N (ticket exists, needs an update), JULY id (already in a July audit,
still true).

### Development (CODE)

| ID | Sev | Where | Issue | Cross-ref |
|----|-----|-------|-------|-----------|
| CODE-1 | high | `toolkit/cli/credentials.py:144`, `toolkit/features/credentials.py:689-750` | `toolkit credentials generate` defaults to `auto_update=False` and prints ~15 plaintext secrets (Grafana admin, CrowdSec key, OIDC client secrets, HMAC/JWT/storage keys) to stdout; also the silent fallback on any SOPS write failure | NEW |
| CODE-2 | high | `apps/api/src/internal/api/healthchecks.go:97-159` | `/health`, `/healthz`, `/ready` share one handler whose database, Redis and external checks are stubs returning "healthy" unconditionally | NEW |
| CODE-3 | medium | `apps/api/src/` | One Go test file (`pkg/config/env_test.go`); zero handler tests for subscribe, unsubscribe, lead-magnet, health | NEW |
| CODE-4 | medium | `apps/api/src/cmd/server/main.go:39` | `r.Run()` with no SIGTERM handling; rollouts hard-kill in-flight Beehiiv/SMTP calls | NEW |
| CODE-5 | low | `apps/api/src/internal/api/healthchecks.go:41` | Health response reports `Service: "cubelab-api"` (pre-rename) | NEW |
| CODE-6 | medium | `.pre-commit-config.yaml` | ruff/mypy hooks scoped to `^toolkit/`; `tests/` has 48 ruff errors incl. 3 B023 closure-over-loop-variable in `test_reusable_workflow_permission_ceiling.py:150-153` | NEW |
| CODE-7 | medium | `pyproject.toml`, untracked `poetry.lock` | `poetry check` and `poetry show --outdated` both fail (lock stale, `mutmut ^3.7.0` unresolvable) | PARTIAL #1128 |
| CODE-8 | medium | `toolkit/features/filesystem.py` | 8 of 13 functions have no caller (single import site uses `ensure_directory` only) | NEW |
| CODE-9 | low | `toolkit/features/validation.py` | 7 of 11 functions have no caller | NEW |
| CODE-10 | low | `toolkit/scripts/sync_homepage_config.py:597` | `build_ascii_topology` defined, never called | NEW |
| C12 | low | `secrets_manager.py:1749` | `sops set` value built by manual quoting, not `json.dumps`; a value containing `"` or `\` corrupts the write | JULY C12 |
| C14 / P14 | low | `Makefile:382-393` | `dev-full-reset` runs `credentials-generate` then blocks on `read -p`; hangs any non-TTY caller | JULY C14 |
| P11 | low | `toolkit/cli/infra.py:1346` | Missing f-string prefix; hint prints literal `{env}` (moved from `:945`, same bug) | JULY P11 |
| P12 | low | `toolkit/cli/sync.py` `_run_with_check` | Snapshot, mutate tracked files, restore; no lock anywhere in the toolkit | JULY P12 |
| P13 | low | `Makefile:1711`, `toolkit/cli/config.py:136` | `make validate` fails on any box without the `terraform` binary, unrelated to config validity | JULY P13 |

Checked and clean: mypy strict passes on 102 files; no bare `except`; one deliberate `shell=True` primitive; CLI exit codes sound on 10 sampled modules; Go module and Dockerfile in good shape; dependabot config deliberate; 1963 tests, all 121 skips carry a reason; `--json` gap already #839; CORS wildcard already #1440.

### Infrastructure best practices (IAC)

| ID | Sev | Where | Issue | Cross-ref |
|----|-----|-------|-------|-----------|
| IAC-1 | high | `common.yaml` `apps.platform.api.version: dev`, no override in `staging.yaml` | Staging `api` renders `kubelab-api:dev`, the mutable alias ADR-046 says no longer exists; consequence of the `api` promotion lane never having run | PARTIAL #1666 |
| IAC-2 | high | `infra/k8s/base/namespace.yaml`, all `base/services/*.yaml` except `edge/errors.yaml` | 17 of 18 workloads (24 containers) have no `securityContext` at pod or container level; namespace carries no Pod Security Standard label | NEW |
| IAC-3 | medium | `infra/k8s/base/services/grafana.yaml` | The only NetworkPolicy in the repo; postgres, redis, minio and 14 other services are reachable from any pod in the namespace | NEW |
| IAC-4 | medium | `infra/ansible/roles/{docker_app,docker_service,health_check,k3s_agent,project_setup,traefik}` | Six Compose-era roles unreachable from any tracked playbook (`generated/` is gitignored and `ansible_run` never resolves into it); `traefik` role also has two tasks with no `changed_when` | NEW |
| IAC-5 | medium | `infra/terraform/*/main.tf` | All 7 roots use `backend "local"`; already lost state once (#1327) | COVERED #558 |
| IAC-6 | low | `.github/workflows/`, `Makefile` | No tflint/tfsec/checkov for any Terraform root; Go and Python get gosec/gitleaks | NEW |

Checked and clean: every GitHub Action SHA-pinned; CronJob hygiene complete; both Dockerfiles hardened (multi-stage or documented, pinned base, numeric non-root user); compose templates SSOT-driven with healthchecks; PDBs irrelevant on a single-node cluster.

### UI, UX and SEO (UX)

| ID | Sev | Where | Issue | Cross-ref |
|----|-----|-------|-------|-----------|
| UX-1 | high | `infra/k8s/base/services/homepage.yaml:112-124` | Cockpit IngressRoute has no `authelia` middleware in either env; would serve node Tailscale IPs and topology unauthenticated. #456 deferred this pending the CrowdSec bouncer, which has since shipped. **Latent today**: UX-2 shows the hostname does not resolve and no wildcard record exists in `records_kubelab.tf`, so landing #967 before #456 is what makes the exposure live. #456 must land first or in the same change | COVERED #456 (blocker cleared, ordering constraint added) |
| UX-2 | high | `homepage.yaml:114`, `infra/terraform/dns/` | Base hardcodes `Host(home.kubelab.live)` for both envs; no Cloudflare record exists for it and no wildcard covers it. #967's stated root cause ("prod patch missing") is wrong: no patch is possible, base emits the prod name. Depends on UX-1 landing first | PARTIAL #967 |
| UX-3 | low | `homepage-config/bookmarks.yaml` | "AWS (~$4/mo)" billing bookmark for a destroyed account; file is hand-maintained, no `.j2` twin | NEW |
| UX-4 | medium | `edge/errors/html/errors/*.html` (9 files) | No `<h1>` in any error page (`<div class="code">`); fails WCAG 2.4.6 | NEW |
| UX-5 | low | same 9 files + `maintenance.html` | No `<meta name="robots">`; nginx `robots.txt` only covers the errors hostname, not the host whose 503 the body is served under | NEW |
| UX-6 | medium | `infra/k8s/base/edge/errors.yaml:85-91`, `edge/errors/nginx.conf` | Traefik intercepts 502-504 only and nginx can only emit 404; 401/403/408/429/500 pages are maintained, branded, and unreachable in both envs | NEW |
| UX-7 | low | `edge/errors/html/errors/404-southpark.webp` | Referenced by nothing (404.html inlines a data URI); shipped in every image | NEW (fold into UX-6) |
| UX-8 | high | GitHub repo metadata | Description "5-node bare-metal cluster: Proxmox, K8s, Ansible, Tailscale. Plus Astro blog."; topics `astro, docker-compose, golang`. Nothing here is true; it is the search-result and social-card text for the portfolio audience | NEW |
| UX-9 | low | GitHub repo settings | GitHub Pages enabled (`build_type: workflow`, `public: true`), `mlorentedev.github.io/kubelab` returns 404, no workflow deploys it | NEW |
| UX-10 | medium | `infra/k8s/base/edge/secure-headers.yaml` | No `X-Robots-Tag` or robots handling on any public admin hostname (grafana, gitea, n8n, argocd, minio, homepage); all on public DNS | NEW, related #675 |
| UX-11 | medium | `Makefile:56,57,885,927` | `provision`/`maintain` help and usage strings omit `gcp1` three months after the cutover | COVERED #1158 (add detail) |
| UX-12 | medium | `Makefile:1512-1514` | `validate-sync` uses `$(or $(filter staging prod,$(ENV)),staging)`: any typo or unset ENV silently checks staging and reports clean | NEW |

Checked and clean: the one Grafana dashboard is valid with no stale references; `apps/wiki/generated_docs` is gitignored build output of a generator that is a no-op today; `make deploy-k8s ENV=bogus` fails fast with a clear message; Vikunja's `bypass` is the documented native-OIDC pattern (ADR-066), not an exposure.

### Content and documentation (DOCS)

| ID | Sev | Where | Issue | Cross-ref |
|----|-----|-------|-------|-----------|
| DOCS-1 | critical | `README.md:25,31,45,72,86,174`; `AGENTS.md:20`; `CLAUDE.md:37-38,148` | All three first-read documents place the Argo CD hub on AWS `t4g.small` / `aws1`. ADR-063: hub is `gcp1`; `aws1` destroyed 2026-08-23 | NEW (#1249 covers code, not prose) |
| D47 / D53 / D68 / D75 | high | `docs/architecture/current-state-2026-03-22.md`, `docs/runbooks/operations.md:221`, `docs/architecture/dash-001-homepage-cockpit.md:84,93,150` | Same aws1 drift in four more files, plus Ollama on three different nodes in one doc; `current-state` still linked as "Current architecture state" from `architecture-overview.md:84` | JULY, now worse |
| DOCS-2 | high | `docs/adr/adr-032-idp-branding-substrate.md` vs `adr-032-observability-stack-execution.md` | Duplicate ADR number; #1677 (2026-09-04) reused 032. `docs/README.md:19` says the filename is the only index | NEW |
| DOCS-3 | high | `CLAUDE.md:77` vs `CLAUDE.md:156,158`; `docs/runbooks/rpi4-sd-card-provisioning.md:21` | CLAUDE.md contradicts itself on `apps.auth.admin_username`: line 77 says the key was removed by #1390; the SSOT-014b block still names it as the mechanism. Code confirms it is gone | NEW |
| P8 | high | `CLAUDE.md:68,90` | Gotchas instruct `make deploy-vps` and `make deploy-dns`; neither target exists (real: `make deploy TARGET=vps`) | JULY P8 |
| DOCS-4 | high | `docs/architecture/service-catalog.md:52,53,68` | Predates ADR-065 (Gitea canonical, still says "mirrors"), ADR-066 (Vikunja row points at "Stream F"), and the act_runner has no entry | NEW |
| D8 / D41 / D88 | high | `toolkit/README.md` | Byte-for-byte unchanged since July: fictional `commands/lib/utils` layout and command groups, none of the real groups documented, and `infra/config/env/` named as SSOT in 10 places (directory does not exist) | JULY, no ticket |
| DOCS-5 | medium | `docs/adr/adr-063-hub-cloud-provider-migration.md:4` | `status: proposed` for a migration executed 2026-08-23 | PARTIAL JULY D54 |
| D54 / D56 / D57 / D58 / D89 | medium | `docs/adr/` | Status vocabulary `active` vs `accepted` (24 vs 34 files), adr-015 `active` though complete, a dated note misfiled as an ADR, no index, adr-018 rejection record marked `active` | JULY |
| D49 | medium | `CHANGELOG.md` | Last entry 2026-03-26; misses ADR-029..066, prod cutover, hub migration, forge. Per-app changelogs are healthy | JULY, no ticket |
| DOCS-6 | medium | `docs/runbooks/rpi4-sd-card-provisioning.md:13,53,80` | Load-bearing step runs `infra/provisioning/rpi4/configure-sd.sh`; `infra/provisioning/` does not exist | NEW |
| P7 | medium | `pre-prod-verification.md`, `deploy-new-k3s-service.md` (`make sops-check`), `rollback-k3s-to-compose.md`, `runbook-disaster-recovery.md`, `dns-homelab.md` | Retired flows still `status: active` with no lifecycle banner | JULY, no ticket |
| D16 / D80 | medium | `docs/runbooks/headscale-setup.md:37,715`, `docker.md:110`, `automation.md:61`, `local-development.md:202` | scp of a repo path that does not exist; "Docker network `proxy`"; `infra/stacks/apps/web/` and `blog` references | JULY (#825/#826) |
| D65 | high | `docs/runbooks/sops-and-secrets.md:352` | Instructs `sops -d common.enc.yaml \| grep api_token`, the decrypt-then-filter pattern CLAUDE.md's secrets doctrine forbids (the whole store reaches stdout and the transcript). Under #826's scope but severity raised here | JULY D65 (#826) |
| DOCS-7 | low | `docs/adr/adr-066-self-hosted-task-platform.md:17` | Links `specs/IDP-035-...`, archived to `specs/archive/` | NEW (fold) |
| D83 / D84 / D86 / D90 | low | `docs/troubleshooting/*`, `testing-guide.md`, `networking-topology.md`, `hardware/nodos-arm.png` | Typos, wrong `pytest.ini` reference, RPi4 interface names, orphaned image | JULY, no ticket |

July docs reconciliation (D1-D92): 32 fixed, 4 partial, 56 still true. The fixes landed exactly where #824/#830 aimed (README, CONTRIBUTING, deployment.md, versioning-strategy.md, cicd.md, proxmox-setup.md). Everything under #825 DOCS-002 (architecture and runbooks rebuild) and #826 DOCS-003 (secrets triad and troubleshooting sweep) is still open and still accurate as scope; both umbrella tickets remain the right home for D3, D4, D9, D12-D19, D26, D29-D38, D44-D46, D48. Lessons index is clean (`toolkit tools lessons-index` reports no drift). Two Spanish hits, both intentional quotes.

### Process and backlog (PROC)

| ID | Sev | Where | Issue | Cross-ref |
|----|-----|-------|-------|-----------|
| PROC-9 | high | `origin/feat/auth-004-identity-ssot` commit `9f0973a4` | `fix(auth): refuse to apply secrets when the identity SSOT is undeclared` (+73 lines, with tests) is not on master. Today `_resolve_superadmin` (`k8s_secrets.py:240`) returns `""` with a warning and `_build_dynamic_literals` silently drops the `grafana-admin`/`minio-secrets` literals; `apply-secrets` reports success and the pod later fails `CreateContainerConfigError`. Verified by content, not hash: the guard string ("resolve from the identity SSOT and it is not declared") is absent from master's `k8s_secrets.py`, and master's `tests/test_admin_identity_ssot.py` is the #1390 version without the 49 lines the commit adds | NEW |
| PROC-1 | high | issue titles | Six AREA-NNN collisions beyond the known TOOL-021: TOOL-064 (#1707/#1635), OBS-019 (#1659/#1395), BACKUP-046 (#1632/#1111), BACKUP-047 (#1572/#1204), SEC-SOPS-001 (#1519/#889), SEC-013 (#1475/#1385). No allocator, no uniqueness check | NEW |
| PROC-6 | high | `specs/TOOL-009-cluster-operator-bootstrap`, `specs/NOTIFY-001` | Both `implementing`/`draft`, both track issues in the knowledge repo that are CLOSED, both features shipped (`cluster_bootstrap:` live; routing table in use). Same class as #1154 (VPNACL-001), which under-states scope | PARTIAL #1154, JULY D60 |
| PROC-2 | medium | issue titles | Three documentation prefixes coexist (DOC, DOCS, DOC-MAINT; DOCS-021..023 are two weeks old); TOOLKIT-001..009 (9 open, bulk-imported 2026-06-11, untouched) describe work the TOOL-* toolkit absorbed; VPN-ACL vs VPNACL | NEW |
| PROC-4 | medium | labels | None of 26 labels encodes priority; zero titles carry P0-P3; priority exists only on the board, which was unreachable all session | NEW |
| PROC-5 | medium | `specs/ANSIBLE-041-aws1-replacement-provisioning`, #1102 | Premise is `make aws1-replace` skipping `provision-aws1.yml`; aws1 is gone and `gcp1-replace` (`Makefile:1343`) already provisions with `node_maintenance` | NEW (close as superseded) |
| PROC-7 | info | `specs/WEB-010-interactive-cv` | Its issue #611 was transferred to `mlorentedev/web#40`; the spec stayed here | NEW (fold into PROC-6) |
| PROC-3 | info | issues | 271 of 508 open issues created 2026-06-11; "zero untouched > 90 days" is true by construction until the cohort ages | NEW (no ticket) |
| PROC-10..14 | medium | knowledge store `10_projects/kubelab/context.md`, `architecture/components/_index.md` | `blocked_by` says "aws1 is running"; hardware inventory omits gcp1; links `console.kubelab.com` (not in SSOT); components index describes kubelab-agents as "OpenClaw + Telegram + Ollama" (all three retired); five `business/execution` docs untouched > 180 days | NEW (vault) |
| branches | low | `origin/{feat/ansible-037-devnode-gitea-access, feature/repoint-argo-route-to-gcp-hub, fix/tool-051-vikunja-oidc-upgrade}` | Merged or superseded, no lost work, safe to delete. Worktrees `kubelab-wt-{lesson-442,linear,sync-error}`: branches merged (#1717, #1709, #1719), trees clean | routine |
| CI | — | last 60 runs | Healthy. `review-attestation` non-success is designed cancellation (0 real failures); the two `""` conclusions in the dump did not reproduce live; 0 open dependabot PRs | no finding |

Near-duplicate title scan: no accidental duplicates; the lettered sub-series convention scores high by design. SEC-007 (#1593) vs AUTH-001 (#900) both concern Authelia password reset and deserve one human read (PLAUSIBLE). IDP-008a-d (#358, #362, #367) describe OpenClaw skills; OpenClaw was retired.

July codebase reconciliation (C1-C16): 11 fixed, 5 still true (C7 narrow, C11, C12, C14, C15). C11 and C15 sit under #833 DEBT-011. July process reconciliation (P1-P15): 4 fixed, 10 still true, 1 obsolete.

---

## 3. Proposed tickets

Grouped by area. IDs are the next free number per prefix computed over all 722
issues (open and closed) so they do not collide (PROC-1). Severity is given;
execution order is deliberately not. Each row lists what it bundles.

### Security and IaC

| ID | Sev | Title | Bundles |
|----|-----|-------|---------|
| [SEC-017 #1733](https://github.com/mlorentedev/kubelab/issues/1733) | high | `toolkit credentials generate` must not default to printing plaintext secrets to stdout | CODE-1 |
| [SEC-018 #1734](https://github.com/mlorentedev/kubelab/issues/1734) | high | Set a pod security baseline (runAsNonRoot, readOnlyRootFilesystem, drop capabilities) across kubelab workloads and label the namespace with a Pod Security Standard | IAC-2 |
| [SEC-019 #1735](https://github.com/mlorentedev/kubelab/issues/1735) | medium | Default-deny NetworkPolicy for the kubelab namespace with per-service allows, starting with postgres, redis, minio | IAC-3 |
| ~~SEC-020~~ **[PR #1732](https://github.com/mlorentedev/kubelab/pull/1732)** | high | Not filed as a ticket: the fix already existed, tested, on `origin/feat/auth-004-identity-ssot`. Cherry-picked onto a fresh branch (that branch predates #1390's squash, so its merge-base is stale) and opened as a PR. Guard proven red by mutation. | PROC-9 |
| [ANSIBLE-058 #1739](https://github.com/mlorentedev/kubelab/issues/1739) | medium | Remove the six Compose-era Ansible roles no tracked playbook can reach | IAC-4 |
| [TF-012 #1740](https://github.com/mlorentedev/kubelab/issues/1740) | low | Add tflint (optionally tfsec/checkov) as a CI gate over `infra/terraform/*` | IAC-6 |

### apps/api

| ID | Sev | Title | Bundles |
|----|-----|-------|---------|
| [DELIVERY-007 #1736](https://github.com/mlorentedev/kubelab/issues/1736) | high | apps/api health handler is mocked: database, Redis and external checks always return healthy | CODE-2, CODE-5 |
| [DELIVERY-008 #1737](https://github.com/mlorentedev/kubelab/issues/1737) | medium | Add handler tests for apps/api (subscribe, unsubscribe, lead-magnet, health) | CODE-3 |
| [DELIVERY-009 #1738](https://github.com/mlorentedev/kubelab/issues/1738) | medium | apps/api graceful shutdown on SIGTERM | CODE-4 |

### Toolkit and process

| ID | Sev | Title | Bundles |
|----|-----|-------|---------|
| ~~TOOL-068~~ → [#833](https://github.com/mlorentedev/kubelab/issues/833) body | medium | Extend ruff/mypy enforcement to `tests/` (48 findings, 3 closure-over-loop-variable) | CODE-6 |
| ~~TOOL-069~~ → [PR #1757](https://github.com/mlorentedev/kubelab/pull/1757) | low | Delete the unused functions in `filesystem.py`, `validation.py` and `build_ascii_topology` | CODE-8, CODE-9, CODE-10 |
| ~~TOOL-070~~ → [PR #1757](https://github.com/mlorentedev/kubelab/pull/1757) | low | Small toolkit correctness fixes: `set_secret` must `json.dumps` its value; missing f-string at `infra.py:1346`; `make validate` must not fail on a missing terraform binary | C12, P11, P13 |
| ~~TOOL-071~~ → [PR #1757](https://github.com/mlorentedev/kubelab/pull/1757) | low | Split the interactive `read -p` out of `make dev-full-reset` | C14, P14 |
| ~~TOOL-072~~ → [#833](https://github.com/mlorentedev/kubelab/issues/833) body | low | Guard `_run_with_check`'s snapshot/mutate/restore window (lock, or compare in memory) | P12 |
| ~~TOOL-073~~ → [#833](https://github.com/mlorentedev/kubelab/issues/833) body | medium | `make validate-sync` must fail on an invalid or unset ENV instead of silently checking staging | UX-12 |
| [TOOL-074 #1743](https://github.com/mlorentedev/kubelab/issues/1743) | high | Ticket-ID hygiene in this repo: resolve the six AREA-NNN collisions, retire DOC/DOC-MAINT/TOOLKIT/VPN-ACL in favour of DOCS/TOOL/VPNACL, and add a repo-local hygiene guard (same shape as the lessons counter) that fails on a duplicate ID. The allocator check at creation time belongs to the `new-ticket` skill in the dotfiles repo and is filed there, not here | PROC-1, PROC-2 |
| [TOOL-075 #1746](https://github.com/mlorentedev/kubelab/issues/1746) | high | Reconcile spec status against tracked-issue state: archive TOOL-009 and NOTIFY-001, decide WEB-010's home, broaden #1154 | PROC-6, PROC-7, D60 |

PROC-4 (no priority signal outside the board) is recorded as an observation and
deliberately not filed: ADR-018 makes the board the SSOT for task state, the
outage that exposed it was largely self-inflicted by this session's own
GraphQL usage, and the memory already records the board-lookup pattern.

### Documentation

| ID | Sev | Title | Bundles |
|----|-----|-------|---------|
| [DOCS-024 #1747](https://github.com/mlorentedev/kubelab/issues/1747) | critical | Sweep the Argo CD hub from AWS/aws1 to GCP/gcp1 across README, AGENTS.md, CLAUDE.md, operations.md, dash-001, current-state (retire or banner the last). Prose only: `networking.aws` in `common.yaml` and `infra/terraform/aws/` are dormant on purpose (`make tf-aws-apply` renders from them) and must not be touched by this sweep | DOCS-1, D47, D53, D68, D75 |
| [DOCS-025 #1748](https://github.com/mlorentedev/kubelab/issues/1748) | high | CLAUDE.md self-consistency: drop the `apps.auth.admin_username` mechanism from SSOT-014b, replace `make deploy-vps`/`deploy-dns` with `make deploy TARGET=…`, fix rpi4-sd-card note | DOCS-3, P8 |
| [DOCS-026 #1749](https://github.com/mlorentedev/kubelab/issues/1749) | high | ADR hygiene: renumber the second adr-032, advance ADR-063, one status vocabulary, banner adr-015 and adr-018, generate an index, fix the adr-066 spec link | DOCS-2, DOCS-5, DOCS-7, D54, D56, D57, D58, D89 |
| [DOCS-027 #1750](https://github.com/mlorentedev/kubelab/issues/1750) | high | Refresh service-catalog.md for ADR-065 and ADR-066 and add act_runner (or fold into #825) | DOCS-4 |
| [DOCS-028 #1751](https://github.com/mlorentedev/kubelab/issues/1751) | high | Regenerate toolkit/README.md from the live CLI tree; `infra/config/env/` does not exist | D8, D41, D88 |
| ~~DOCS-029~~ → [#825](https://github.com/mlorentedev/kubelab/issues/825) body | medium | CHANGELOG.md: resume from release tags or mark retired | D49 |
| ~~DOCS-030~~ → [#825](https://github.com/mlorentedev/kubelab/issues/825) body | medium | Runbook lifecycle sweep: rpi4-sd-card phantom script, `make sops-check`, status banners on five retired runbooks, headscale-setup scp path, small accuracy fixes, orphaned image | DOCS-6, P7, D16, D83, D84, D86, D90 |
| (vault, no ticket) | medium | Refresh `10_projects/kubelab/context.md` and `architecture/components/_index.md` against ADR-063, AI-007, ADR-044. Disposition: patched directly in the knowledge store in the session that files these tickets, not tracked on the board (vault content is not repo work) | PROC-10..14 |

### UX and SEO

| ID | Sev | Title | Bundles |
|----|-----|-------|---------|
| [OPS-029 #1752](https://github.com/mlorentedev/kubelab/issues/1752) | high | Rewrite the GitHub repository description and topics for the current IDP; disable GitHub Pages or deploy something behind it | UX-8, UX-9 |
| [OPS-030 #1753](https://github.com/mlorentedev/kubelab/issues/1753) | medium | Error pages: add an `h1` and a robots meta tag, decide the fate of the five pages Traefik never serves, drop the orphaned webp | UX-4, UX-5, UX-6, UX-7 |
| ~~OPS-031~~ → [#675](https://github.com/mlorentedev/kubelab/issues/675) body | medium | `X-Robots-Tag: noindex` on admin hostnames via secure-headers (or a checklist item on #675) | UX-10 |
| ~~DASH-011~~ → half [PR #1757](https://github.com/mlorentedev/kubelab/pull/1757), half declined (§3c) | low | Drop the AWS billing bookmark and make bookmarks.yaml SSOT-driven like services.yaml | UX-3 |

### Updates to existing tickets (comments, no new issue)

| Ticket | Update |
|--------|--------|
| #456 DASH-007e | Blocker (CrowdSec bouncer) shipped; Homepage Authelia middleware can proceed | UX-1 |
| #967 DASH-002 | Root cause is not a missing prod patch: base emits `home.kubelab.live` for both envs and no DNS record exists in either | UX-2 |
| #1158 DEBT-016 | Add the gcp1 omission at `Makefile:56,57,885,927` | UX-11 |
| #1666 | Add AC: `staging.yaml` carries an explicit `apps.platform.api.version` once the lane runs, verified on the render | IAC-1 |
| #1128 DEBT-015 | Attach the `poetry check` / `poetry show --outdated` reproduction | CODE-7 |
| #1154 VPNACL-001 | Broaden to the class (or supersede by TOOL-075) | PROC-6 |
| #1102 ANSIBLE-041 | Close as superseded by `gcp1-replace`; archive the spec | PROC-5 |
| #675 | Add search-indexing control as a checklist item | UX-10 |
| #834 OPS-013 | This report is the second pass it asked for; close it with the PR that lands this file, listing the tickets above as the follow-ups | all |

### Routine cleanup (no ticket)

Delete the three zombie remote branches and remove the three merged worktrees.
Read each once more before deleting: PROC-9 shows a "merged" branch can carry an
unmerged commit.

---

---

## 3b. Corrections to this report (2026-09-07, during ticket filing)

Two findings were re-measured while writing their tickets and did not survive.
Recorded here rather than silently edited above, because how they failed is the
transferable part.

### UX-2 is wrong: the DNS record exists

The report asserts "no Cloudflare record exists for it and no wildcard covers it",
having read `infra/terraform/dns/records_kubelab.tf`. That file contains no literal
`home` — because it does not contain any literal service name. It builds records
with `for_each = local.kubelab_services`, sourced from
`infra/terraform/dns/services.json`, which carries:

```json
{"name": "home", "zone": "kubelab", "proxied": false, "environments": ["prod"]}
```

and the record is present in `terraform.tfstate`. **Reading the `.tf` and not its
input produced a confident negative.** The general form: a generated artefact
cannot be audited by grepping the generator.

**What is true instead**, read off `kubectl kustomize` rather than the patches:
the prod patch at `overlays/prod/patches.yaml:299` **exists and is a byte-identical
no-op** — it overrides ``Host(`home.kubelab.live`)`` with the same value. Both
overlays render the same hostname, so staging claims the prod name and there is no
staging cockpit hostname at all.

### UX-1 is inverted: the exposure is live, not latent

UX-1 called the missing Authelia middleware "latent today" **because of UX-2's
wrong premise**. With the record present, measured 2026-09-07:

```
dig +short home.kubelab.live @1.1.1.1   -> 162.55.57.175
curl -I https://home.kubelab.live/      -> HTTP/2 200, no auth redirect
/api/services 200 · /api/bookmarks 200 · /api/widgets 200   (all unauthenticated)
```

**Calibrated: information disclosure, not a control surface.** It publishes the
admin hostname inventory (`argo`, `grafana`, `n8n`, `traefik`, `traefik.staging`,
`status`) — all of which already have public DNS and public Let's Encrypt certs
and are therefore enumerable from crt.sh — plus `100.64.0.10`, which is CGNAT and
unroutable. Checked explicitly and **absent**: any service declaring a `widget`
(zero), and `/api/proxy` (404). Homepage's server-side widget proxy is what would
have made this a genuine P1, by letting an unauthenticated visitor drive
authenticated calls to Grafana or n8n through the cockpit.

Recorded on #456, with a recommendation to raise it to P1 — not for the disclosure,
but because its stated blocker (the CrowdSec bouncer) shipped and the thing is
serving. Note #967's body records a deliberate 2026-08-10 decision to make the
cockpit public; the public half was executed and the auth half was not.

### The lesson both share

Both errors are the same shape as the one the report itself warns about for
Kustomize ("verify by reading the emitted object, never the patch"). The audit
applied that discipline to K8s and not to Terraform. **An audit finding stated as
an absence — "no record exists", "nothing references this" — is only as good as
the completeness of the search that produced it**, and a `for_each` over a JSON
file is exactly the indirection a grep for a literal name will miss.

---

## 3c. Disposition of every finding

Filed as tickets (17), all carrying the `audit-2026-09-07` label:

| # | Findings bundled |
|---|---|
| [#1733](https://github.com/mlorentedev/kubelab/issues/1733) SEC-017 | CODE-1 |
| [#1734](https://github.com/mlorentedev/kubelab/issues/1734) SEC-018 | IAC-2 |
| [#1735](https://github.com/mlorentedev/kubelab/issues/1735) SEC-019 | IAC-3 |
| [#1736](https://github.com/mlorentedev/kubelab/issues/1736) DELIVERY-007 | CODE-2, CODE-5 |
| [#1737](https://github.com/mlorentedev/kubelab/issues/1737) DELIVERY-008 | CODE-3 |
| [#1738](https://github.com/mlorentedev/kubelab/issues/1738) DELIVERY-009 | CODE-4 |
| [#1739](https://github.com/mlorentedev/kubelab/issues/1739) ANSIBLE-058 | IAC-4 |
| [#1740](https://github.com/mlorentedev/kubelab/issues/1740) TF-012 | IAC-6 |
| [#1743](https://github.com/mlorentedev/kubelab/issues/1743) TOOL-074 | PROC-1, PROC-2 |
| [#1746](https://github.com/mlorentedev/kubelab/issues/1746) TOOL-075 | PROC-6, PROC-7, D60 |
| [#1747](https://github.com/mlorentedev/kubelab/issues/1747) DOCS-024 | DOCS-1, D47, D53, D68, D75 |
| [#1748](https://github.com/mlorentedev/kubelab/issues/1748) DOCS-025 | DOCS-3, P8 |
| [#1749](https://github.com/mlorentedev/kubelab/issues/1749) DOCS-026 | DOCS-2, DOCS-5, DOCS-7, D54, D56, D57, D58, D89 |
| [#1750](https://github.com/mlorentedev/kubelab/issues/1750) DOCS-027 | DOCS-4 |
| [#1751](https://github.com/mlorentedev/kubelab/issues/1751) DOCS-028 | D8, D41, D88 |
| [#1752](https://github.com/mlorentedev/kubelab/issues/1752) OPS-029 | UX-8, UX-9 |
| [#1753](https://github.com/mlorentedev/kubelab/issues/1753) OPS-030 | UX-4, UX-5, UX-6, UX-7 |

Fixed in [PR #1757](https://github.com/mlorentedev/kubelab/pull/1757) rather than
filed — each smaller than its own ticket: **C12, P11, P13, C14/P14, CODE-8,
CODE-9, CODE-10, UX-3, UX-7**.

Fixed in [PR #1732](https://github.com/mlorentedev/kubelab/pull/1732): **PROC-9**.

Added to an existing umbrella's body as acceptance criteria — a thread comment on
a 500-issue backlog is indistinguishable from "no ticket":

| Umbrella | Findings |
|---|---|
| [#825](https://github.com/mlorentedev/kubelab/issues/825) DOCS-002 | D49, DOCS-6, P7, D16/D80, D83, D84, D86, D90 |
| [#833](https://github.com/mlorentedev/kubelab/issues/833) DEBT-011 | CODE-6, P12, UX-12 |
| [#675](https://github.com/mlorentedev/kubelab/issues/675) | UX-10 |

Recorded as a comment on an existing ticket: **UX-1** (#456), **UX-2** (#967),
**UX-11** (#1158), **IAC-1** (#1666), **CODE-7** (#1128), **PROC-6** (#1154),
**PROC-5** (#1102), **D65** severity raised (#826).

Already covered, nothing added: **IAC-5** (#558), CORS wildcard (#1440), `--json`
gap (#839).

Deliberately not filed, as a stated decision: **PROC-3** (the 2026-06-11 import
cohort makes "zero stale issues" true by construction — an observation about a
metric, not work) and **PROC-4** (no priority signal outside the board; ADR-018
makes the board the SSOT for task state, and the outage that exposed it was this
session's own GraphQL usage).

Sent to the knowledge store rather than the board: **PROC-10..14** (vault content
is not repo work).

**Declined, with the reason recorded** — the second half of DASH-011, "make
`bookmarks.yaml` SSOT-driven like `services.yaml`". The AWS bookmark is removed in
PR #1757; the generation half is not being done and is not being filed. The two
files are not the same kind of thing: `services.yaml` lists kubelab services, whose
names, ports and hostnames are already declared in `common.yaml`, so generating it
removes a second copy of a fact. `bookmarks.yaml` is a list of **external** links —
Cloudflare, Hetzner, GitHub, the Obsidian vault — which have no declaration in
`common.yaml` and would have to be invented as config to be generated from it. That
trades a hand-edited YAML file for a hand-edited YAML file plus a generator. Revisit
if a bookmark ever needs to carry a value that `common.yaml` already owns.

Routine, no ticket: three zombie remote branches and three merged worktrees.

## 4. Not covered

- The bitácora board (priority, status, in-review columns): GraphQL exhausted.
- Full bodies of all 508 open issues: cross-referencing used titles, bodies by
  grep, and REST search on key nouns for every high or critical NEW finding.
- The extracted web repo, and `apps/wiki/generated_docs` (untracked build
  output).
- Compose stacks under `infra/stacks/` beyond four spot checks; `traefik_vps`
  port bindings (dormant post-cutover).
- Cyclomatic complexity by tool; `infra.py` (2216 lines) and
  `secrets_manager.py` (1922) are the files to start with if wanted.
- D80's full runbook list: 19 of ~25 sampled.
- SEC-007 vs AUTH-001 duplicate status.
- `ansible-lint`, `tflint`, `tfsec` were not run locally.
