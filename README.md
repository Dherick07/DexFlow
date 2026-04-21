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
