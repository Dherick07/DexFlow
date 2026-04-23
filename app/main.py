from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.automations_registry import AUTOMATIONS, featured, grouped_by_client
from app.routers import capspace as capspace_router
from app.routers import chemika as chemika_router
from app.routers import primebuild as primebuild_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="DexFlow", description="Dexterous Group automation hub")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Make sidebar_groups available to every template render via Jinja globals,
# so per-automation router files don't need to pass it in every context.
templates.env.globals["sidebar_groups"] = grouped_by_client()

app.include_router(capspace_router.router, prefix="/capspace", tags=["capspace"])
app.include_router(chemika_router.router, prefix="/chemika", tags=["chemika"])
app.include_router(primebuild_router.router, prefix="/primebuild", tags=["primebuild"])


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "featured_automations": featured()},
    )


@app.get("/automations", response_class=HTMLResponse)
async def automations(request: Request):
    return templates.TemplateResponse(
        "automations.html",
        {"request": request, "automations": AUTOMATIONS},
    )


@app.get("/healthz", response_class=PlainTextResponse)
async def healthz():
    return "ok"
