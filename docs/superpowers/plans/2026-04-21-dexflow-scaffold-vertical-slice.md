# DexFlow — Scaffold + CI/CD + Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship DexFlow scaffold with CI/CD deployed to a DigitalOcean droplet, one working automation (Chemika Invoice TXT Formatter), and all plumbing proven end-to-end.

**Architecture:** FastAPI + Jinja2 + Tailwind CDN + Alpine.js, packaged in Docker, fronted by Caddy, deployed via GitHub Actions → GHCR → SSH. Modular folder structure by client. In-memory file handling; no disk persistence.

**Tech Stack:** Python 3.12, FastAPI, uvicorn, pandas, openpyxl, Jinja2, Tailwind (CDN), Alpine.js (CDN), Docker, Docker Compose, Caddy, GitHub Actions, GitHub Container Registry.

**Project root:** `C:\Users\jaydh\Documents\Projects\Dherick07_Github_Projects\DexFlow`

**Source of truth for lifted code:** `C:\Users\jaydh\Documents\Projects\Dherick07_Github_Projects\Handover_automations\Chemika\Chemika-Payroll-Txtfile-Automations\app.py`

---

## File Structure Overview

At the end of this plan, the repo contains:

```
DexFlow/
├── .github/
│   └── workflows/
│       └── deploy.yml                    # CI/CD pipeline
├── app/
│   ├── __init__.py                       # Package marker
│   ├── main.py                           # FastAPI app, mounts routers, home page
│   ├── routers/
│   │   ├── __init__.py
│   │   └── chemika.py                    # /chemika/* routes
│   ├── services/
│   │   ├── __init__.py
│   │   └── chemika.py                    # Lifted Chemika business logic
│   ├── templates/
│   │   ├── base.html                     # Shared layout (nav, Tailwind/Alpine)
│   │   ├── home.html                     # Landing page
│   │   └── chemika/
│   │       └── invoice_txt.html          # Upload form
│   └── static/
│       └── custom.css                    # Any styles Tailwind can't do
├── tests/
│   └── fixtures/
│       └── chemika/
│           └── invoice_txt/
│               ├── input.xlsx            # Known-good input (binary)
│               └── expected_output.txt   # Expected output from original Streamlit app
├── docs/
│   └── superpowers/
│       ├── plans/                         # This file lives here
│       └── specs/                         # Design spec lives here
├── .dockerignore
├── .gitignore
├── Caddyfile
├── CLAUDE.md                              # Already exists; do not modify
├── Dockerfile
├── README.md
├── docker-compose.yml
└── requirements.txt
```

---

## Task 1: Initialize Git Repo and Create `.gitignore`

**Files:**
- Create: `DexFlow/.gitignore`
- Create: `DexFlow/README.md`

- [ ] **Step 1: Initialize git in the DexFlow directory**

```bash
cd "C:/Users/jaydh/Documents/Projects/Dherick07_Github_Projects/DexFlow"
git init
git branch -m main
```

Expected: `Initialized empty Git repository` and branch renamed to `main`.

- [ ] **Step 2: Create `.gitignore`**

Path: `DexFlow/.gitignore`

Content:
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
.Python
.venv/
venv/
env/
.pytest_cache/

# Environment / secrets
.env
.env.local
*.pem
*.key

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp

# Docker build artefacts
*.log
```

- [ ] **Step 3: Create a minimal `README.md`**

Path: `DexFlow/README.md`

Content:
```markdown
# DexFlow

Unified FastAPI web app consolidating Dexterous Group's internal accounting automations (Capspace, Chemika, Primebuild, Sales Invoicing). Deployed on a DigitalOcean droplet via Docker Compose.

## Scope

**Phase 1a (current):** Port 9 Streamlit automation endpoints to FastAPI. No auth. Internal-only.
**Phase 1b (post-Bien):** Microsoft SSO + request logging + HTTPS.
**Phase 2 (future):** KPI dashboard.

See `docs/superpowers/specs/2026-04-21-dexflow-design.md` for the full design.

## Local Development

```bash
# With Docker (recommended)
docker compose up --build

# Without Docker
python -m venv .venv
source .venv/bin/activate        # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000

## Deployment

Push to `main` → GitHub Actions builds Docker image → pushes to GHCR → SSHs to droplet → `docker compose pull && up -d`.
```

- [ ] **Step 4: Commit**

```bash
git add .gitignore README.md
git commit -m "chore: initial repo scaffold (gitignore, README)"
```

Expected: 1 commit, 2 files.

---

## Task 2: Create Python Package Skeleton and `requirements.txt`

**Files:**
- Create: `DexFlow/requirements.txt`
- Create: `DexFlow/app/__init__.py`
- Create: `DexFlow/app/routers/__init__.py`
- Create: `DexFlow/app/services/__init__.py`

- [ ] **Step 1: Create `requirements.txt`**

Path: `DexFlow/requirements.txt`

Content:
```
fastapi==0.115.0
uvicorn[standard]==0.32.0
jinja2==3.1.4
python-multipart==0.0.12
pandas==2.2.3
openpyxl==3.1.5
xlsxwriter==3.2.0
numpy==2.1.2
```

Pinned versions for reproducibility. Only these dependencies for now; anything new must be flagged before install per CLAUDE.md rules.

- [ ] **Step 2: Create `app/__init__.py`**

Path: `DexFlow/app/__init__.py`

Content:
```python
```
(Empty file — package marker only.)

- [ ] **Step 3: Create `app/routers/__init__.py`**

Path: `DexFlow/app/routers/__init__.py`

Content:
```python
```
(Empty file — package marker only.)

- [ ] **Step 4: Create `app/services/__init__.py`**

Path: `DexFlow/app/services/__init__.py`

Content:
```python
```
(Empty file — package marker only.)

- [ ] **Step 5: Commit**

```bash
git add requirements.txt app/
git commit -m "chore: add Python package skeleton and requirements.txt"
```

---

## Task 3: Create FastAPI `main.py` with Home Route

**Files:**
- Create: `DexFlow/app/main.py`

- [ ] **Step 1: Write `main.py`**

Path: `DexFlow/app/main.py`

Content:
```python
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="DexFlow", description="Dexterous Group automation hub")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/healthz", response_class=PlainTextResponse)
async def healthz():
    return "ok"
```

- [ ] **Step 2: Verify import works locally**

Run:
```bash
cd "C:/Users/jaydh/Documents/Projects/Dherick07_Github_Projects/DexFlow"
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
python -c "from app.main import app; print(app.title)"
```

Expected output: `DexFlow`

If this fails with an import error, the template directory doesn't exist yet — that's expected, continue to Task 4 which creates it. The import will succeed once templates exist.

*Note: the `python -c` line above references templates that don't exist yet — it will fail at runtime. Skip this step if it errors; Task 4 fixes it.*

- [ ] **Step 3: Commit**

```bash
git add app/main.py
git commit -m "feat: add FastAPI app with home route and healthz"
```

---

## Task 4: Create Base Layout Template

**Files:**
- Create: `DexFlow/app/templates/base.html`
- Create: `DexFlow/app/static/custom.css`

- [ ] **Step 1: Create `app/static/custom.css`**

Path: `DexFlow/app/static/custom.css`

Content:
```css
/* Overrides for anything Tailwind cannot do. Empty by default. */
```

- [ ] **Step 2: Create `app/templates/base.html`**

Path: `DexFlow/app/templates/base.html`

Content:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}DexFlow{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js"></script>
    <link rel="stylesheet" href="/static/custom.css">
</head>
<body class="bg-slate-50 text-slate-900 min-h-screen">
    <header class="bg-white border-b border-slate-200">
        <div class="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
            <a href="/" class="text-xl font-semibold text-slate-900">DexFlow</a>
            <span class="text-sm text-slate-500">Dexterous Group automation hub</span>
        </div>
    </header>
    <main class="max-w-5xl mx-auto px-6 py-8">
        {% block content %}{% endblock %}
    </main>
    <footer class="max-w-5xl mx-auto px-6 py-6 text-center text-sm text-slate-400">
        DexFlow &middot; Internal tooling
    </footer>
</body>
</html>
```

- [ ] **Step 3: Commit**

```bash
git add app/templates/base.html app/static/custom.css
git commit -m "feat: add base layout template with Tailwind and Alpine"
```

---

## Task 5: Create Home Page Template

**Files:**
- Create: `DexFlow/app/templates/home.html`

- [ ] **Step 1: Create `home.html`**

Path: `DexFlow/app/templates/home.html`

Content:
```html
{% extends "base.html" %}

{% block title %}DexFlow — Automations{% endblock %}

{% block content %}
<h1 class="text-3xl font-semibold mb-2">Automations</h1>
<p class="text-slate-600 mb-8">Select an automation to run. Upload the required file(s); download the processed output.</p>

<section class="space-y-8">

    <div>
        <h2 class="text-xl font-semibold text-slate-800 mb-3">Chemika</h2>
        <ul class="space-y-2">
            <li>
                <a href="/chemika/invoice-txt" class="block bg-white border border-slate-200 rounded-lg px-4 py-3 hover:border-blue-400 hover:shadow-sm transition">
                    <div class="font-medium">Invoice TXT Formatter</div>
                    <div class="text-sm text-slate-500">Convert invoice spreadsheet into tab-delimited .txt for accounting import.</div>
                </a>
            </li>
        </ul>
    </div>

</section>
{% endblock %}
```

Only Chemika Invoice TXT is listed — other automations are added in Plan 2 as they're ported.

- [ ] **Step 2: Run app locally and verify home page**

```bash
cd "C:/Users/jaydh/Documents/Projects/Dherick07_Github_Projects/DexFlow"
.venv/Scripts/activate
uvicorn app.main:app --reload
```

Open http://localhost:8000 in a browser. Expected: DexFlow header, "Automations" heading, one card ("Invoice TXT Formatter"). Clicking it should 404 (router not yet built — that's fine).

Also test: open http://localhost:8000/healthz → `ok`.

Stop the server with Ctrl+C.

- [ ] **Step 3: Commit**

```bash
git add app/templates/home.html
git commit -m "feat: add home page listing Chemika Invoice TXT"
```

---

## Task 6: Create Dockerfile

**Files:**
- Create: `DexFlow/Dockerfile`
- Create: `DexFlow/.dockerignore`

- [ ] **Step 1: Create `.dockerignore`**

Path: `DexFlow/.dockerignore`

Content:
```
.git
.gitignore
.venv/
venv/
__pycache__/
*.pyc
.pytest_cache/
tests/
docs/
.github/
README.md
.env
*.md
!CLAUDE.md
```

- [ ] **Step 2: Create `Dockerfile`**

Path: `DexFlow/Dockerfile`

Content:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Build image locally to verify**

```bash
cd "C:/Users/jaydh/Documents/Projects/Dherick07_Github_Projects/DexFlow"
docker build -t dexflow:local .
```

Expected: image builds successfully. Final line: `Successfully tagged dexflow:local`.

- [ ] **Step 4: Run container and verify**

```bash
docker run --rm -p 8000:8000 dexflow:local
```

In a second terminal:
```bash
curl http://localhost:8000/healthz
```

Expected: `ok`

Stop the container with Ctrl+C.

- [ ] **Step 5: Commit**

```bash
git add Dockerfile .dockerignore
git commit -m "feat: add Dockerfile with Python 3.12 slim + uvicorn"
```

---

## Task 7: Create Docker Compose + Caddyfile

**Files:**
- Create: `DexFlow/docker-compose.yml`
- Create: `DexFlow/Caddyfile`

- [ ] **Step 1: Create `docker-compose.yml`**

Path: `DexFlow/docker-compose.yml`

Content:
```yaml
services:
  app:
    image: ghcr.io/${GITHUB_REPOSITORY:-dherick07/dexflow}:latest
    build: .
    restart: unless-stopped
    expose:
      - "8000"
    environment:
      - ENV=production

  caddy:
    image: caddy:2.8
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - app

volumes:
  caddy_data:
  caddy_config:
```

The `image:` + `build:` combo means: in CI, pull `image` from GHCR; locally, build from the Dockerfile if the image isn't present. `${GITHUB_REPOSITORY:-...}` picks up the repo path in CI; falls back to a default locally.

- [ ] **Step 2: Create `Caddyfile` (Phase 1a, no domain)**

Path: `DexFlow/Caddyfile`

Content:
```
:80 {
    reverse_proxy app:8000

    # Generous timeouts for long-running Excel processing
    request_body {
        max_size 50MB
    }
}
```

The `request_body max_size 50MB` is a safety net — none of the automations should need this, but it prevents accidental cuts on larger batch files.

- [ ] **Step 3: Run docker compose locally**

```bash
cd "C:/Users/jaydh/Documents/Projects/Dherick07_Github_Projects/DexFlow"
docker compose up --build -d
```

Wait ~10 seconds, then verify:
```bash
curl http://localhost/healthz
```

Expected: `ok` (note: port 80, not 8000, because we're going through Caddy).

Check logs:
```bash
docker compose logs app | tail -20
docker compose logs caddy | tail -20
```

Expected: both containers started without errors.

- [ ] **Step 4: Tear down**

```bash
docker compose down
```

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml Caddyfile
git commit -m "feat: add docker-compose with Caddy reverse proxy"
```

---

## Task 8: Create GitHub Repo and Push

**Files:**
- (Remote repo setup only; no local files.)

- [ ] **Step 1: Create private repo on GitHub**

Using GitHub CLI (install `gh` if not present: https://cli.github.com/):
```bash
cd "C:/Users/jaydh/Documents/Projects/Dherick07_Github_Projects/DexFlow"
gh repo create dexflow --private --source=. --remote=origin
```

Or manually: go to github.com/new, create `dexflow` as **private**, then:
```bash
git remote add origin git@github.com:<your-username>/dexflow.git
```

- [ ] **Step 2: Push main branch**

```bash
git push -u origin main
```

Expected: all commits pushed; GitHub repo populated.

- [ ] **Step 3: Verify repo is private**

Visit `https://github.com/<your-username>/dexflow` in a browser. Expected: repo visible to you, a lock icon next to the name. No anonymous access.

---

## Task 9: Create CI/CD Workflow

**Files:**
- Create: `DexFlow/.github/workflows/deploy.yml`

- [ ] **Step 1: Create `.github/workflows/deploy.yml`**

Path: `DexFlow/.github/workflows/deploy.yml`

Content:
```yaml
name: Build and Deploy

on:
  push:
    branches: [main]
  workflow_dispatch: {}

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Set lowercase image name
        id: image
        run: echo "name=ghcr.io/${GITHUB_REPOSITORY,,}" >> "$GITHUB_OUTPUT"

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ steps.image.outputs.name }}:latest
            ${{ steps.image.outputs.name }}:${{ github.sha }}

      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.DROPLET_HOST }}
          username: ${{ secrets.DROPLET_USER }}
          key: ${{ secrets.DROPLET_SSH_KEY }}
          script: |
            cd /opt/dexflow
            git pull
            docker compose pull
            docker compose up -d
            docker image prune -f
```

Notes:
- GHCR image names must be lowercase; the `image` step normalises the repo path.
- `docker image prune -f` at the end cleans up old image layers so the droplet disk doesn't fill up.

- [ ] **Step 2: Commit and push**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: add build-and-deploy workflow for GHCR + SSH"
git push
```

After push: the workflow triggers but **will fail** at the SSH step — secrets and droplet don't exist yet. That's expected. Proceed to Task 10.

---

## Task 10: Droplet — One-Time Setup

**Files:**
- (Droplet-side commands; no local files.)

Assumes a DigitalOcean Ubuntu 22.04 droplet is already provisioned. If not, provision one first: $6/mo basic, Sydney region (closest to Australia).

- [ ] **Step 1: SSH in as root (first time only)**

From your local machine:
```bash
ssh root@<droplet-ip>
```

- [ ] **Step 2: Create `deploy` user**

On the droplet:
```bash
adduser --disabled-password --gecos "" deploy
usermod -aG sudo deploy
```

- [ ] **Step 3: Install Docker and Docker Compose**

On the droplet (as root):
```bash
apt-get update
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Verify:
```bash
docker --version
docker compose version
```

Expected: both print version numbers.

- [ ] **Step 4: Add `deploy` to docker group**

On the droplet:
```bash
usermod -aG docker deploy
```

- [ ] **Step 5: Generate SSH key pair for CI on your local machine**

On your local machine (NOT the droplet):
```bash
ssh-keygen -t ed25519 -C "dexflow-ci" -f ~/.ssh/dexflow_deploy -N ""
```

Two files produced:
- `~/.ssh/dexflow_deploy` (private key — goes in GitHub secret)
- `~/.ssh/dexflow_deploy.pub` (public key — goes on the droplet)

- [ ] **Step 6: Install public key on the droplet for the `deploy` user**

Copy the contents of `~/.ssh/dexflow_deploy.pub` (from your local machine).

On the droplet (as root):
```bash
mkdir -p /home/deploy/.ssh
echo "<paste public key contents here>" >> /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
```

- [ ] **Step 7: Test SSH as deploy user**

From your local machine:
```bash
ssh -i ~/.ssh/dexflow_deploy deploy@<droplet-ip> "docker ps"
```

Expected: successful login, empty `docker ps` output (no containers running yet).

- [ ] **Step 8: Clone DexFlow repo into `/opt/dexflow`**

Log in as `deploy`:
```bash
ssh -i ~/.ssh/dexflow_deploy deploy@<droplet-ip>
```

Then on the droplet:
```bash
sudo mkdir -p /opt/dexflow
sudo chown deploy:deploy /opt/dexflow
cd /opt/dexflow
git clone https://github.com/<your-username>/dexflow.git .
```

You'll be prompted for credentials. Use a GitHub Personal Access Token (create one at https://github.com/settings/tokens with `repo` scope).

After clone, switch to SSH URL for future `git pull`s — or cache the HTTPS creds:
```bash
git config credential.helper store
git pull        # enter PAT once; stored for future
```

- [ ] **Step 9: Log in to GHCR from droplet**

Create a second PAT with `read:packages` scope (from https://github.com/settings/tokens). Then on the droplet:
```bash
echo "<ghcr-pat>" | docker login ghcr.io -u <your-username> --password-stdin
```

Expected: `Login Succeeded`.

---

## Task 11: Add GitHub Secrets and Trigger First Deploy

**Files:**
- (GitHub settings only; no local files.)

- [ ] **Step 1: Add GitHub repository secrets**

Go to `https://github.com/<your-username>/dexflow/settings/secrets/actions`. Add three secrets:

| Name | Value |
|---|---|
| `DROPLET_HOST` | The droplet's IP address (e.g. `165.22.xx.xx`) |
| `DROPLET_USER` | `deploy` |
| `DROPLET_SSH_KEY` | The **entire contents** of `~/.ssh/dexflow_deploy` (the private key, including the `-----BEGIN` and `-----END` lines) |

- [ ] **Step 2: Trigger a new deploy**

On your local machine:
```bash
cd "C:/Users/jaydh/Documents/Projects/Dherick07_Github_Projects/DexFlow"
git commit --allow-empty -m "ci: trigger first deploy"
git push
```

- [ ] **Step 3: Watch the workflow**

```bash
gh run watch
```

Or go to `https://github.com/<your-username>/dexflow/actions`.

Expected: all three steps (Build, Push, SSH Deploy) complete successfully.

- [ ] **Step 4: Verify the droplet is serving the home page**

From your local machine:
```bash
curl http://<droplet-ip>/healthz
curl -s http://<droplet-ip>/ | grep -o "<title>.*</title>"
```

Expected: `ok` for the first call, `<title>DexFlow — Automations</title>` for the second.

Also open `http://<droplet-ip>/` in a browser. Expected: styled home page showing "Chemika → Invoice TXT Formatter".

**Milestone:** pipeline is proven end-to-end. Scaffold, Docker, CI, droplet, Caddy, Tailwind all working. Next task ports the first automation.

- [ ] **Step 5: Commit (empty — milestone marker)**

```bash
git commit --allow-empty -m "chore: milestone — scaffold deployed, pipeline proven"
git push
```

---

## Task 12: Lift Chemika Invoice TXT Service

**Files:**
- Create: `DexFlow/app/services/chemika.py`

- [ ] **Step 1: Create `app/services/chemika.py`**

Path: `DexFlow/app/services/chemika.py`

This is lifted verbatim from `Handover_automations/Chemika/Chemika-Payroll-Txtfile-Automations/app.py` lines 685-737, with docstring added and no other modifications.

Content:
```python
"""Chemika business logic.

Lifted from Handover_automations/Chemika/app.py as-is per the 'wrap, don't
rewrite' rule. Only the pure functions are copied; Streamlit calls are dropped.
"""

import pandas as pd


def txt_format_date(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    if isinstance(val, pd.Timestamp):
        return val.strftime("%d/%m/%Y")
    try:
        return pd.to_datetime(val).strftime("%d/%m/%Y")
    except Exception:
        return str(val)


def txt_clean_num(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    f = float(val)
    return str(int(f)) if f == int(f) else str(f)


def build_txt(
    df: pd.DataFrame,
    memo: str,
    due_date: int,
    due_days: int,
    tax_code: str,
    account: str,
) -> bytes:
    TAB, CRLF = "\t", "\r\n"
    required = ["Date", "Sub Total", "GST", "Company Name", "Invoice Number"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: '{col}'")
    df = df.copy()
    if "Other" not in df.columns:
        df["Other"] = ""
    df = df.sort_values(
        by=["Company Name", "Invoice Number"],
        key=lambda col: col.astype(str) if col.name == "Company Name"
                        else pd.to_numeric(col, errors="coerce").fillna(0),
    )
    header = TAB.join([
        "Date", "Sub Total", "Other", "GST", "Company Name", "Invoice Number",
        "Memo", "TT Ex GST", "TT Inc GST", "Due Date", "Due Days", "Tax Code", "Account",
    ])
    blank = TAB * 12
    lines = [header]
    for _, row in df.iterrows():
        date_str = txt_format_date(row["Date"])
        sub_total = txt_clean_num(row["Sub Total"])
        other = txt_clean_num(row.get("Other", ""))
        gst = txt_clean_num(row["GST"])
        company = str(row["Company Name"]).strip()
        invoice = str(int(row["Invoice Number"])) if pd.notna(row["Invoice Number"]) else ""
        try:
            tt_ex_str = txt_clean_num(float(row["Sub Total"]))
            tt_inc_str = txt_clean_num(float(row["Sub Total"]) + float(row["GST"]))
        except Exception:
            tt_ex_str, tt_inc_str = sub_total, ""
        lines.append(TAB.join([
            date_str, sub_total, other, gst, company, invoice,
            memo, tt_ex_str, tt_inc_str,
            str(due_date), str(due_days), tax_code, account,
        ]))
        lines.append(blank)
    return (CRLF.join(lines)).encode("utf-8")
```

- [ ] **Step 2: Verify it imports without error**

```bash
cd "C:/Users/jaydh/Documents/Projects/Dherick07_Github_Projects/DexFlow"
.venv/Scripts/activate
python -c "from app.services.chemika import build_txt; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add app/services/chemika.py
git commit -m "feat(chemika): lift Invoice TXT service from Streamlit"
```

---

## Task 13: Create Chemika Router

**Files:**
- Create: `DexFlow/app/routers/chemika.py`

- [ ] **Step 1: Create `app/routers/chemika.py`**

Path: `DexFlow/app/routers/chemika.py`

Content:
```python
from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.services import chemika as chemika_service

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

router = APIRouter()

ALLOWED_INVOICE_EXT = {".xlsx", ".xls", ".csv"}


@router.get("/invoice-txt", response_class=HTMLResponse)
async def invoice_txt_form(request: Request):
    return templates.TemplateResponse(
        "chemika/invoice_txt.html",
        {"request": request, "error": None},
    )


@router.post("/invoice-txt")
async def invoice_txt_submit(
    request: Request,
    file: UploadFile = File(...),
    memo: str = Form(""),
    account: str = Form(""),
    due_date: int = Form(0),
    due_days: int = Form(0),
    tax_code: str = Form(""),
):
    filename = file.filename or "upload"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_INVOICE_EXT:
        return templates.TemplateResponse(
            "chemika/invoice_txt.html",
            {
                "request": request,
                "error": f"Expected .xlsx, .xls, or .csv — got '{ext}'.",
            },
            status_code=400,
        )

    try:
        raw = await file.read()
        buffer = BytesIO(raw)
        if ext == ".csv":
            df = pd.read_csv(buffer)
        else:
            df = pd.read_excel(buffer)
    except Exception as exc:
        return templates.TemplateResponse(
            "chemika/invoice_txt.html",
            {"request": request, "error": f"Couldn't read file: {exc}"},
            status_code=400,
        )

    try:
        output = chemika_service.build_txt(
            df=df,
            memo=memo,
            due_date=due_date,
            due_days=due_days,
            tax_code=tax_code,
            account=account,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            "chemika/invoice_txt.html",
            {"request": request, "error": str(exc)},
            status_code=400,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Processing error: {exc}")

    out_name = Path(filename).stem + ".txt"
    return StreamingResponse(
        BytesIO(output),
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'},
    )
```

- [ ] **Step 2: Mount the router in `main.py`**

Edit `app/main.py`. Locate the imports block and add:

```python
from app.routers import chemika as chemika_router
```

Locate the block below `templates = Jinja2Templates(...)` and before the `@app.get("/")` route. Add:

```python
app.include_router(chemika_router.router, prefix="/chemika", tags=["chemika"])
```

After the edit, `main.py` should look like:

```python
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routers import chemika as chemika_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="DexFlow", description="Dexterous Group automation hub")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

app.include_router(chemika_router.router, prefix="/chemika", tags=["chemika"])


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/healthz", response_class=PlainTextResponse)
async def healthz():
    return "ok"
```

- [ ] **Step 3: Verify imports**

```bash
cd "C:/Users/jaydh/Documents/Projects/Dherick07_Github_Projects/DexFlow"
.venv/Scripts/activate
python -c "from app.main import app; print([r.path for r in app.routes])"
```

Expected output (order may vary):
```
['/openapi.json', '/docs', '/docs/oauth2-redirect', '/redoc', '/static', '/chemika/invoice-txt', '/chemika/invoice-txt', '/', '/healthz']
```

The `/chemika/invoice-txt` appears twice because both GET and POST are registered.

- [ ] **Step 4: Commit**

```bash
git add app/routers/chemika.py app/main.py
git commit -m "feat(chemika): add invoice-txt router with upload form and submit"
```

---

## Task 14: Create Chemika Invoice TXT Template

**Files:**
- Create: `DexFlow/app/templates/chemika/invoice_txt.html`

- [ ] **Step 1: Create template directory and file**

Path: `DexFlow/app/templates/chemika/invoice_txt.html`

Content:
```html
{% extends "base.html" %}

{% block title %}Chemika — Invoice TXT Formatter{% endblock %}

{% block content %}
<nav class="text-sm text-slate-500 mb-4">
    <a href="/" class="hover:text-blue-600">Home</a>
    <span class="mx-1">/</span>
    <span>Chemika</span>
    <span class="mx-1">/</span>
    <span class="text-slate-700">Invoice TXT Formatter</span>
</nav>

<h1 class="text-2xl font-semibold mb-2">Invoice TXT Formatter</h1>
<p class="text-slate-600 mb-6">
    Upload an invoice spreadsheet (.xlsx, .xls, .csv). Required columns:
    <code class="bg-slate-100 px-1 rounded">Date</code>,
    <code class="bg-slate-100 px-1 rounded">Sub Total</code>,
    <code class="bg-slate-100 px-1 rounded">GST</code>,
    <code class="bg-slate-100 px-1 rounded">Company Name</code>,
    <code class="bg-slate-100 px-1 rounded">Invoice Number</code>.
    Output: tab-delimited .txt ready for accounting import.
</p>

{% if error %}
<div class="bg-red-50 border border-red-200 text-red-800 rounded-lg px-4 py-3 mb-6">
    <strong>Error:</strong> {{ error }}
</div>
{% endif %}

<form method="POST" enctype="multipart/form-data" class="bg-white border border-slate-200 rounded-lg p-6 space-y-5"
      x-data="{ submitting: false }" @submit="submitting = true">

    <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">Invoice spreadsheet</label>
        <input type="file" name="file" accept=".xlsx,.xls,.csv" required
               class="block w-full text-sm border border-slate-300 rounded-md file:bg-slate-100 file:border-0 file:px-4 file:py-2 file:mr-4 file:text-sm file:font-medium">
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Memo</label>
            <input type="text" name="memo" value=""
                   class="block w-full text-sm border border-slate-300 rounded-md px-3 py-2">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Account code</label>
            <input type="text" name="account" value=""
                   class="block w-full text-sm border border-slate-300 rounded-md px-3 py-2">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Due Date (days)</label>
            <input type="number" name="due_date" value="0" min="0"
                   class="block w-full text-sm border border-slate-300 rounded-md px-3 py-2">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Due Days</label>
            <input type="number" name="due_days" value="0" min="0"
                   class="block w-full text-sm border border-slate-300 rounded-md px-3 py-2">
        </div>
        <div class="md:col-span-2">
            <label class="block text-sm font-medium text-slate-700 mb-1">Tax Code</label>
            <input type="text" name="tax_code" value=""
                   class="block w-full text-sm border border-slate-300 rounded-md px-3 py-2">
        </div>
    </div>

    <button type="submit"
            :disabled="submitting"
            class="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
        <span x-show="!submitting">Process and Download</span>
        <span x-show="submitting" x-cloak>Processing…</span>
    </button>
</form>
{% endblock %}
```

- [ ] **Step 2: Run app locally and verify form renders**

```bash
cd "C:/Users/jaydh/Documents/Projects/Dherick07_Github_Projects/DexFlow"
.venv/Scripts/activate
uvicorn app.main:app --reload
```

Open http://localhost:8000/chemika/invoice-txt. Expected: styled form with file input, memo, account, due_date, due_days, tax_code fields and a blue "Process and Download" button.

Click home link → should navigate back to home page.

Stop server with Ctrl+C.

- [ ] **Step 3: Commit**

```bash
git add app/templates/chemika/invoice_txt.html
git commit -m "feat(chemika): add invoice-txt upload form template"
```

---

## Task 15: Create Test Fixture for Chemika Invoice TXT

**Files:**
- Create: `DexFlow/tests/fixtures/chemika/invoice_txt/input.xlsx` (binary — engineer generates)
- Create: `DexFlow/tests/fixtures/chemika/invoice_txt/expected_output.txt` (binary — engineer generates)
- Create: `DexFlow/tests/fixtures/chemika/invoice_txt/README.md`

- [ ] **Step 1: Create fixture directory**

```bash
cd "C:/Users/jaydh/Documents/Projects/Dherick07_Github_Projects/DexFlow"
mkdir -p tests/fixtures/chemika/invoice_txt
```

- [ ] **Step 2: Generate `input.xlsx` using the original Streamlit app as the source of truth**

The fixture must produce byte-identical output from both the original Streamlit app and the new FastAPI service. Use a real invoice spreadsheet from Dher's actual Chemika work, or construct a small synthetic one.

Minimum fixture columns:
- `Date` — three dates (e.g. `01/04/2026`, `15/04/2026`, `20/04/2026`)
- `Sub Total` — decimal numbers
- `GST` — decimal numbers
- `Company Name` — 2 distinct companies
- `Invoice Number` — ascending integers

Save as `tests/fixtures/chemika/invoice_txt/input.xlsx`.

- [ ] **Step 3: Generate `expected_output.txt` by running the original Streamlit app**

```bash
cd "C:/Users/jaydh/Documents/Projects/Dherick07_Github_Projects/Handover_automations/Chemika/Chemika-Payroll-Txtfile-Automations"
streamlit run app.py
```

In the Streamlit UI:
1. Click the "Invoice TXT Formatter" tab.
2. Upload the `input.xlsx` from the DexFlow fixtures folder.
3. Fill in form fields: `memo=test-memo`, `account=1234`, `due_date=30`, `due_days=7`, `tax_code=GST`.
4. Click the download button — save as `expected_output.txt` in `DexFlow/tests/fixtures/chemika/invoice_txt/`.

- [ ] **Step 4: Create a README describing the fixture**

Path: `DexFlow/tests/fixtures/chemika/invoice_txt/README.md`

Content:
```markdown
# Chemika Invoice TXT Fixture

## Source

Generated from the original Streamlit app at
`Handover_automations/Chemika/Chemika-Payroll-Txtfile-Automations/app.py`
on <date generated>.

## Form parameters used

- memo = `test-memo`
- account = `1234`
- due_date = `30`
- due_days = `7`
- tax_code = `GST`

## How to re-verify

Upload `input.xlsx` to DexFlow's `/chemika/invoice-txt` endpoint with the above
form fields. The downloaded `.txt` must byte-match `expected_output.txt`.
```

- [ ] **Step 5: Commit fixture**

```bash
git add tests/fixtures/chemika/invoice_txt/
git commit -m "test(chemika): add invoice-txt fixture from original Streamlit app"
```

---

## Task 16: Local Smoke Test Against Fixture

**Files:**
- (No files; verification only.)

- [ ] **Step 1: Run DexFlow locally**

```bash
cd "C:/Users/jaydh/Documents/Projects/Dherick07_Github_Projects/DexFlow"
.venv/Scripts/activate
uvicorn app.main:app --reload
```

- [ ] **Step 2: Submit the fixture via `curl`**

In a second terminal:
```bash
cd "C:/Users/jaydh/Documents/Projects/Dherick07_Github_Projects/DexFlow"
curl -X POST http://localhost:8000/chemika/invoice-txt \
  -F "file=@tests/fixtures/chemika/invoice_txt/input.xlsx" \
  -F "memo=test-memo" \
  -F "account=1234" \
  -F "due_date=30" \
  -F "due_days=7" \
  -F "tax_code=GST" \
  -o /tmp/dexflow_output.txt
```

Expected: file saved to `/tmp/dexflow_output.txt`, no HTTP error.

- [ ] **Step 3: Diff against expected output**

```bash
diff /tmp/dexflow_output.txt tests/fixtures/chemika/invoice_txt/expected_output.txt
```

Expected: **no output** (files are byte-identical).

If there's any diff, debug by comparing line-by-line:
```bash
cmp /tmp/dexflow_output.txt tests/fixtures/chemika/invoice_txt/expected_output.txt
```

The most likely cause of a diff is line-ending mismatch — the Chemika service explicitly writes `\r\n`, and `curl -o` on Windows may or may not translate. Inspect with:
```bash
hexdump -C /tmp/dexflow_output.txt | head -5
hexdump -C tests/fixtures/chemika/invoice_txt/expected_output.txt | head -5
```

Both should show `0d 0a` at line endings.

- [ ] **Step 4: Stop the server**

Ctrl+C in the first terminal.

- [ ] **Step 5: Commit (empty — smoke test passed)**

```bash
git commit --allow-empty -m "chore: Chemika Invoice TXT smoke test passes locally"
```

---

## Task 17: Deploy to Droplet and Verify in Production

**Files:**
- (No files; deployment + verification.)

- [ ] **Step 1: Push to main — triggers CI deploy**

```bash
git push
```

- [ ] **Step 2: Watch the workflow**

```bash
gh run watch
```

Expected: build, push, SSH deploy all succeed.

- [ ] **Step 3: Verify production home page lists Chemika Invoice TXT**

```bash
curl -s http://<droplet-ip>/ | grep "Invoice TXT Formatter"
```

Expected: HTML snippet containing the link.

- [ ] **Step 4: Run production smoke test**

```bash
cd "C:/Users/jaydh/Documents/Projects/Dherick07_Github_Projects/DexFlow"
curl -X POST http://<droplet-ip>/chemika/invoice-txt \
  -F "file=@tests/fixtures/chemika/invoice_txt/input.xlsx" \
  -F "memo=test-memo" \
  -F "account=1234" \
  -F "due_date=30" \
  -F "due_days=7" \
  -F "tax_code=GST" \
  -o /tmp/dexflow_prod_output.txt
```

- [ ] **Step 5: Diff production output against expected**

```bash
diff /tmp/dexflow_prod_output.txt tests/fixtures/chemika/invoice_txt/expected_output.txt
```

Expected: no output (byte-identical).

- [ ] **Step 6: Check container logs for errors**

```bash
ssh -i ~/.ssh/dexflow_deploy deploy@<droplet-ip> "cd /opt/dexflow && docker compose logs app | tail -30"
```

Expected: logs show the `POST /chemika/invoice-txt 200` line with no tracebacks.

- [ ] **Step 7: Browser manual test**

Open `http://<droplet-ip>/` in a browser. Navigate to Invoice TXT Formatter. Upload the fixture `input.xlsx` using the form, enter the same values as the fixture README. Download should start; save file; open it; eyeball the first few lines look right.

- [ ] **Step 8: Final commit — milestone marker**

```bash
git commit --allow-empty -m "chore: milestone — Chemika Invoice TXT live in production"
git push
```

**End of Plan 1.** Pipeline proven end-to-end. Remaining 8 endpoints follow the same pattern — covered in Plan 2.

---

## What Plan 2 Will Cover

Per the spec's migration order:
1. Chemika Payroll Extractor (same client pattern)
2. Capspace (3 endpoints batched — shared dicts)
3. Primebuild Hours Worked
4. Primebuild Keypay Location
5. Sales Invoicing Part 1
6. Primebuild Payroll Journals (last — do while Bien is still around)

Plan 2 gets written after Plan 1 ships, once we've debugged any real pipeline gotchas and can copy-paste with confidence.

---

## Out of Scope for This Plan

- Microsoft SSO (Phase 1b)
- HTTPS / Let's Encrypt (Phase 1b, after domain is live)
- Request logging / SQLite (Phase 1b)
- Remaining 8 automations (Plan 2)
- Any refactor of hardcoded dicts (tech debt, deferred)
- pytest / CI test step (Phase 1b)
