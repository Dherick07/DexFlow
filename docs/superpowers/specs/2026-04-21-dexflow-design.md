# DexFlow — Architecture Design

> **Date:** 2026-04-21
> **Author:** Dher (with Claude)
> **Status:** Approved (awaiting spec review)

## Overview

DexFlow is a unified FastAPI web app that consolidates four Streamlit-based accounting automations (Capspace, Sales Invoicing Part 1, Chemika, Primebuild) onto a single Docker Compose deployment on a DigitalOcean droplet. The goal for Phase 1a is to ship all ~9 automation endpoints with working parity to the existing Streamlit apps, reviewed and approved by Bien before he leaves (~week of 2026-04-27).

Core principle: **wrap, don't rewrite.** Business logic is lifted as-is from existing Streamlit `app.py` files; only the UI glue is replaced.

## Scope

### Phase 1a — Migration (this week, Bien-reviewable)
- All 9 automation endpoints ported from Streamlit to FastAPI
- Deployed to DigitalOcean via Docker Compose + Caddy
- CI/CD via GitHub Actions (build → push GHCR → deploy via SSH)
- No auth, no persistent DB, no tracking
- **Terminal state:** Bien confirms endpoints match Streamlit outputs

### Phase 1b — SSO + Tracking (immediately post-Bien)
- Microsoft/Azure AD SSO
- HTTPS via Let's Encrypt (auto, via Caddy)
- SQLite request log: user, automation, timestamp, duration, success/failure
- Estimated 2–3 focused days

### Phase 2 — KPI Dashboard (future, only if justified)
- Build a dashboard over the request log
- Not committed; only if volume justifies it

## Users

Internal only. "Clients" = Dexterous Group accountants and internal teams. No external client access.

## Architecture

### Approach: Modular by Client

One FastAPI router per client, one service module per client, one template folder per client. Matches the URL structure 1:1.

### Folder Structure

```
DexFlow/
├── app/
│   ├── main.py                    # FastAPI app, mounts routers, serves home
│   ├── routers/
│   │   ├── capspace.py            # routes for /capspace/*
│   │   ├── primebuild.py          # routes for /primebuild/*
│   │   ├── chemika.py             # routes for /chemika/*
│   │   └── sales_invoicing.py     # routes for /sales-invoicing/*
│   ├── services/
│   │   ├── capspace.py            # lifted from Handover_automations/Capspace/app.py
│   │   ├── primebuild.py
│   │   ├── chemika.py
│   │   └── sales_invoicing.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── capspace/
│   │   │   ├── unit_register.html
│   │   │   ├── loan_register.html
│   │   │   └── interest_payments.html
│   │   ├── primebuild/
│   │   ├── chemika/
│   │   └── sales_invoicing/
│   └── static/
│       └── custom.css
├── tests/
│   └── fixtures/                  # known-good input/output pairs per automation
├── docs/
│   └── superpowers/specs/         # this file lives here
├── .github/
│   └── workflows/
│       └── deploy.yml
├── Dockerfile
├── docker-compose.yml
├── Caddyfile
├── requirements.txt
├── .gitignore
├── README.md
└── CLAUDE.md
```

### URL Structure

| URL | Purpose |
|---|---|
| `/` | Landing page — grouped list of all 9 automations |
| `/capspace/unit-register` | Capspace Unit Register (Tab 1) |
| `/capspace/loan-register` | Capspace Loan Register (Tab 2) |
| `/capspace/interest-payments` | Capspace Interest Payments (Tab 3) |
| `/chemika/payroll-extractor` | Chemika Payroll Extractor |
| `/chemika/invoice-txt` | Chemika Invoice TXT Formatter |
| `/primebuild/payroll-journals` | Primebuild Payroll Journals |
| `/primebuild/hours-worked` | Primebuild Hours Worked |
| `/primebuild/keypay-location` | Primebuild Keypay Location |
| `/sales-invoicing/cm-billing` | Sales Invoicing Part 1 — CM Billing |
| `/healthz` | Health check for Caddy / uptime checks |

### Separation of Concerns

- **Routers** know FastAPI; they translate HTTP ↔ function calls. They don't contain business logic.
- **Services** know nothing about FastAPI. Pure functions: `(inputs) -> BytesIO`. Can be called directly from scripts or tests.
- **Templates** know nothing about processing. Jinja2 only.

## Request Data Flow

```
1. Browser    GET /<client>/<automation>
              → Router renders upload-form template

2. Browser    POST /<client>/<automation> with UploadFile(s) + any form fields
              → Router:
                - validates file extensions
                - reads UploadFile(s) into BytesIO (in-memory)
                - calls services.<client>.<function>(files, params)

3. Service    - Pure function; loads workbook from BytesIO
              - Runs lifted processing logic
              - Returns BytesIO (Excel) or BytesIO (ZIP)

4. Router     Wraps BytesIO in StreamingResponse with:
              - correct media_type (xlsx / zip / txt)
              - Content-Disposition: attachment; filename="..."

5. Browser    Downloads file
```

### Key Choices

- **In-memory, not disk.** All file I/O uses `BytesIO`. No temp files created explicitly. (FastAPI's `UploadFile` may spool to `/tmp` internally for files > 1MB; `/tmp` is inside the container and destroyed on restart.)
- **Synchronous request/response.** No background jobs, no polling, no WebSockets. Matches existing Streamlit UX.
- **ZIP outputs** (Sales Invoicing, Primebuild) use the same pattern — `BytesIO` of zip, `media_type: application/zip`.
- **Caddy/uvicorn timeouts** set to 300s explicitly to cover the longest automation (Primebuild Journals with batch files).

## Error Handling

Philosophy: **fail loudly, fail helpfully.** Internal users; real error messages are more useful than opaque placeholders.

| Failure mode | Behavior |
|---|---|
| Wrong file extension | Router validates before calling service. Returns 400, renders error on form: *"Expected .xlsx, got .docx"* |
| Corrupt / malformed Excel | Service raises. Router catches, shows error on form page with the raw exception message. User re-uploads. |
| Edge case in logic (e.g. missing LOAN_MASTER entry) | Service raises with context. Router shows message. Dher updates dict, redeploys. |
| Timeout | Caddy/uvicorn 300s limit. Rare in practice. User sees timeout error. |
| Uncaught exception | FastAPI exception handler catches, logs full traceback to stdout (via `docker logs`), shows user a short error with "please contact Dher" fallback. |

### Logging

Every request logs a single line to stdout (captured by Docker):

```
[2026-04-21T10:23:45] POST /capspace/unit-register | 200 | 1247ms | files=1
[2026-04-21T10:24:12] POST /primebuild/payroll-journals | 500 | 487ms | error="KeyError: 'NSW'"
```

`docker compose logs -f app` shows live tail. Sufficient for Phase 1a. Proper structured logging (JSON, shipped to a log service) is a Phase 1b+ concern.

## UI Stack

Tailwind CSS (via CDN) + Alpine.js (via CDN) + Jinja2 server-rendered templates. No build step. No npm. No compilation.

```html
<!-- base.html head -->
<script src="https://cdn.tailwindcss.com"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js"></script>
<link rel="stylesheet" href="/static/custom.css">
```

**Rationale:** Tailwind is the de facto target for ui-ux-pro-max output; any AI-generated designs will work natively. Alpine.js handles interactivity (loading states, form validation, toasts) at ~15KB. No build pipeline means no DevOps friction for Phase 1a.

The actual screen designs (landing page layout, per-automation form styling, error states) will be produced using the `ui-ux-pro-max` skill during implementation.

## Deployment Topology

Two containers on the droplet, managed by a single `docker-compose.yml`:

```
                    ┌─────────────── DigitalOcean droplet ────────────────┐
                    │                                                      │
    Browser ──HTTPS─┼───► Caddy :443 ──reverse proxy──► app :8000          │
                    │     (container)                   (container)        │
                    │     auto-SSL via Let's Encrypt                       │
                    │                                                      │
                    └──────────────────────────────────────────────────────┘
```

### Container responsibilities

**`app` container (Python 3.12 slim + FastAPI):**
- Runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- No host port exposed — only reachable via Caddy
- Stateless: container restart loses nothing

**`caddy` container (Caddy official image):**
- Listens on :80 and :443
- Reverse proxies to `app:8000` via docker-compose internal network
- Auto-fetches Let's Encrypt cert once a domain is pointed at the droplet
- Persistent volumes for cert storage: `caddy_data`, `caddy_config`

### Caddyfile

**Phase 1a (pre-domain, droplet IP only):**
```
:80 {
    reverse_proxy app:8000
}
```

**Phase 1b (post-domain):**
```
dexflow.dexterousgroup.com.au {
    reverse_proxy app:8000
}
```

### Dockerfile (app)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Droplet one-time setup

- Create `deploy` user, add to `docker` group, install SSH public key
- Install Docker + Docker Compose
- `docker login ghcr.io` with a PAT scoped to `read:packages`
- Clone DexFlow to `/opt/dexflow` (for compose + Caddyfile)
- Ask IT to add DNS A record: `dexflow.dexterousgroup.com.au` → droplet IP (GoDaddy)

## CI/CD

**GitHub Actions on push to `main`:**

```
1. Actions runner checks out code
2. Logs into ghcr.io using GITHUB_TOKEN
3. Builds Docker image
4. Pushes to ghcr.io/<owner>/dexflow:latest
5. SSHs to droplet as `deploy` user
6. On droplet: `cd /opt/dexflow && git pull && docker compose pull && docker compose up -d`

The `git pull` step keeps `docker-compose.yml` and `Caddyfile` on the droplet in sync with the repo. The actual app code lives in the Docker image, pulled separately.
```

### GitHub Secrets required

- `DROPLET_HOST` — droplet IP (Phase 1a) / hostname (Phase 1b)
- `DROPLET_USER` — `deploy`
- `DROPLET_SSH_KEY` — private key for the `deploy` user
- `GITHUB_TOKEN` — auto-provided by Actions (used to push to GHCR)

### Repo / image visibility

**Private repo + private GHCR image.** Business logic references real client/employee names in hardcoded dicts (Capspace `LOAN_MASTER`, Chemika `EMPLOYEES`); a public repo leaks client data.

## Migration Strategy

### Order: Vertical slice first, then repeat

Port **one automation fully end-to-end first** — scaffold + Docker + CI + deploy + smoke test. Discover all infra gotchas on the simplest endpoint. Then copy-paste the pattern for the remaining 8.

| # | Automation | Rationale |
|---|---|---|
| 1 | Chemika Invoice TXT Formatter | Simplest logic; ideal tracer bullet |
| 2 | Chemika Payroll Extractor | Same client; complex validation but well-structured |
| 3 | Capspace (all 3 tabs batched) | Dicts ported once, reused across 3 endpoints |
| 4 | Primebuild Hours Worked | Medium effort; build familiarity |
| 5 | Primebuild Keypay Location | Medium; classification rules lift cleanly |
| 6 | Sales Invoicing Part 1 | Complex inputs (3-sheet workbook) |
| 7 | Primebuild Payroll Journals | Hardest (ROL rules, dim2 parsing); do while Bien is available |

### Per-automation checklist

1. Copy original `app.py` from `Handover_automations/<client>/...` as reference
2. Create `app/services/<client>.py` — paste only the pure functions (everything not touching `st.*`)
3. Replace Streamlit inputs with function parameters (`st.file_uploader` → `BytesIO`)
4. Create `app/routers/<client>.py` — routes calling the service
5. Create `app/templates/<client>/<automation>.html` — upload form
6. Add entry to home page template
7. Smoke-test locally against a fixture; diff against Streamlit output
8. Commit → push → auto-deploys via CI

## Testing

**Smoke tests only for Phase 1a.** For each automation, keep a `tests/fixtures/<client>/<automation>/` folder with:
- `input.xlsx` (or input files) — known-good input
- `expected_output.xlsx` — output from the existing Streamlit app on the same input

Before each migration commit: manually run the endpoint against the fixture, compare outputs. If functionally equivalent, ship.

**No pytest, no CI test step for Phase 1a.** Rationale: we're porting working code verbatim. Risk is porting errors, not logic errors — manual diff catches those. Proper unit tests + CI tests come in Phase 1b.

## Dependencies

Starting `requirements.txt`:

```
fastapi
uvicorn[standard]
jinja2
python-multipart
pandas
openpyxl
xlsxwriter
numpy
```

Rule: any new dependency beyond this list is flagged for approval before install.

## Key Decisions Log

| Decision | Choice | Reason |
|---|---|---|
| Framework | FastAPI | Dher's strongest framework; aligns with `feedback_fastapi_framework` memory |
| Architecture | Modular by client | Matches URL structure; scales as new automations are added |
| Auth (Phase 1a) | None | Bien can't validate auth code; separates what he can review from what he can't |
| Auth (Phase 1b) | Microsoft Azure AD SSO | Everyone has O365; matches Dexterous infra |
| Hosting | DO droplet + Docker Compose | Matches n8n pattern; full control; no App Platform request timeouts |
| Reverse proxy | Caddy | Auto HTTPS with Let's Encrypt, zero config |
| UI stack | Tailwind CDN + Alpine.js + Jinja2 | No build step; ui-ux-pro-max native target |
| File handling | In-memory BytesIO | No disk cleanup; privacy win; files are small |
| CI/CD | GitHub Actions → GHCR → SSH deploy | Modern; portable; good learning for Dher |
| Repo visibility | Private | Contains real client/employee data in dicts |
| SSH user | Non-root `deploy` | Limits blast radius if CI key leaks |
| Testing | Fixture-based smoke tests | Fast; adequate for Phase 1a; proper tests in Phase 1b |

## Risks

1. **Timeline** — Docker + CI/CD + 9 endpoint migrations + Bien walkthrough in ~5-7 working days is tight. Any unexpected blocker (Docker build issue, CI auth snag, DNS delay) eats migration time.
2. **Primebuild Payroll Journals complexity** — ROL routing logic is the most complex. Schedule a dedicated walkthrough with Bien before he leaves.
3. **Hardcoded dicts** — `LOAN_MASTER`, `UNIT_MASTER`, `EMPLOYEES` port as-is but are technical debt. Don't try to solve this during Phase 1a.
4. **Chemika LeStrange cell-color logic** — depends on Excel fill color; may not survive round-trips. Confirm with Chemika client whether this edge case is still active before migrating Tab 1.
5. **DNS propagation** — subdomain request to IT needs to go out now; GoDaddy propagation can take hours. Caddy HTTPS is gated on DNS being live.

## Out of Scope (explicit)

- Sales Invoicing Part 2 (n8n — already running separately; stays as-is)
- Sales Invoicing Part 3 (in development by Bien)
- Auth / user management (Phase 1b)
- Request logging / KPI dashboard (Phase 1b / 2)
- Refactoring the hardcoded dicts to config files or DB (tech debt, not Phase 1a)
- Chemika `app backup.py` diff / Primebuild `app 02042026.py` diff (note as investigation in Phase 1a migration if time allows; otherwise defer)
- Any automation not currently in the 4-app handover scope

## Related Documents

- [[00 Wiki/Patterns/Self-Hosted-Automation-Hub]] — the broader pattern this project implements
- [[00 Wiki/Domain/Handover-Automations]] — technical detail on each of the 4 source automations
- [[00 Wiki/Domain/Sales-Invoicing-Part2]] — the n8n workflow explicitly out of scope
- `/CLAUDE.md` — project-specific Claude context
