# DexFlow

DexFlow is a unified FastAPI web app that consolidates four Streamlit-based accounting automations (Capspace, Sales Invoicing Part 1, Chemika, Primebuild) onto a single self-hosted DigitalOcean droplet. Built by Dher at Dexterous Group. The goal is to migrate all ~9 automation endpoints from standalone Streamlit apps into a clean FastAPI application — same core logic, different delivery layer.

## Claude's Role

- Architecture and implementation partner — help design the FastAPI structure, write endpoint scaffolding, and port Streamlit apps to API endpoints
- Scope guardian — flag immediately if anything is getting complex instead of shipped
- Dependency advisor — never add packages without flagging first
- If a session is drifting from shipping endpoints to over-engineering, nudge: "Is this needed to ship DexFlow, or is it polish?"

## Process

### Phase 1a — Migration (this week, ends with Bien's approval)
1. Architecture plan — define FastAPI structure, hosting approach, routing
2. Scaffold — create FastAPI app skeleton, basic routing, health check
3. Port automations — migrate each Streamlit app's business logic into endpoints (all 4 automations, ~9 endpoints)
4. Deploy — get it running on DigitalOcean droplet
5. Approval — walkthrough with Bien before he leaves (~week of 2026-04-27)

**Phase 1a has NO auth.** Bien is reviewing automation correctness, which doesn't require auth. Adding auth in this window jeopardizes the migration timeline and Bien can't validate auth code anyway.

### Phase 1b — SSO + Tracking (immediately after Bien leaves)
1. Add Microsoft/Azure AD SSO (all staff have O365)
2. Set up HTTPS via Let's Encrypt + reverse proxy (Caddy or Nginx)
3. Add SQLite request log: user, automation, timestamp, duration, success/failure
4. Announce to accountants: "login added so you can track your runs"

**Estimated:** 2–3 focused days without deadline pressure.

### Phase 1c — UI Refinement (after most/all automations ported, same session)
1. Run `ui-ux-pro-max` skill on all templates
2. Apply Dexterous Group branding — logo, colour palette, typography
3. Goal: modern, polished internal tool feel — clean but unmistakably Dexterous
4. Scope: templates only (`base.html`, per-automation pages) — no logic changes

**Trigger:** After the majority of automations are ported in Phase 1a, before or alongside Phase 1b SSO work.

### Phase 2 — KPI Dashboard (future, only if justified)
Log analysis + dashboard. May not be needed if basic SQLite log is sufficient for reporting.

See [[00 Wiki/Patterns/Self-Hosted-Automation-Hub]] for the full pattern.

## Key People

- **Dher** — builder and owner
- **Bien** — outgoing teammate, original author of all 4 automations, approver before departure (~week of 2026-04-27)

## Automations in Scope

| Automation | Endpoints | Notes |
|---|---|---|
| Capspace | 3 (Unit Register, Loan Register, Interest Payments) | UNIT_MASTER and LOAN_MASTER are hardcoded dicts — don't fix during migration, note as tech debt |
| Sales Invoicing Part 1 | 1 | FF/NFF logic is case-insensitive — preserve this tolerance |
| Chemika | 2 (Payroll Extractor, Invoice TXT Formatter) | LeStrange cell-color logic won't survive CSV round-trip — flag with client before migrating |
| Primebuild | 3 (Payroll Journals, Hours Worked, Keypay Location) | Journals has the most complex routing logic (ROL rules) — get walkthrough from Bien |

**Out of scope:** Sales Invoicing Part 2 (n8n, already running separately), Part 3 (in development).

## Rules & Conventions

- **FastAPI only** — Python web backend is always FastAPI. No Flask, no Django.
- **Don't touch automation logic** — Core processing functions from the Streamlit apps are not to be modified unless explicitly asked. Wrap, don't rewrite.
- **No scope creep** — Flag immediately if the solution is getting complex. Ship working, not perfect.
- **Ask before new dependencies** — Don't add new packages without flagging first.
- **`(C)` prefix** — Files created by Claude are prefixed with `(C)` so they're clearly AI-generated.
- **Editing rule** — Before editing any file without the `(C)` prefix, ask for permission first.

## Testing

A smoke test runner lives at `tests/run_tests.py`. It sends real HTTP requests to the running app and compares outputs against Bien's expected files in `tests/`.

**Run it:**
```bash
pip install requests   # one-time
uvicorn app.main:app --reload
python tests/run_tests.py
```

| Test | File | Status |
|---|---|---|
| Chemika Invoice TXT | `tests/Chemika/Invoice_TXT_Formatter/` | Pass |
| Capspace Unit Register | `tests/Capspace/Unit Register/` | Pass |
| Capspace Loan Register | `tests/Capspace/Loans Register/` | Pass |
| Capspace Interest Payments | `tests/Capspace/Interest Payments/` | Pass |

Actual outputs are saved to `tests/actual/` on each run for manual inspection.

## Current Status

> **Last updated:** 2026-04-23
> **Ported (8/9 endpoints):** Capspace ×3, Chemika ×2, Primebuild ×3. Sales Invoicing Part 1 remains outstanding.
> **Smoke-tested against Bien's reference data:** Capspace ×3 + Chemika Invoice TXT (all passing). Chemika Payroll Extractor and Primebuild ×3 still need HTTP smoke tests against reference outputs.
> **Phase 1c UI restyle:** Complete for all 8 ported endpoints via [PR #6](https://github.com/Dherick07/DexFlow/pull/6) — LearnHub-dialect claymorphism, registry-driven sidebar, public landing + featured-4 home + all-8 automations catalog. Template/CSS only — no automation logic touched. 12/12 pytest tests passing (registry + route smoke tests). Browser-level visual QA pending.
> **Next up:** Merge PR #6 → port Sales Invoicing Part 1 → smoke-test remaining 4 endpoints → Bien walkthrough (~week of 2026-04-27).

<!-- TODO: Update this as the project progresses -->
