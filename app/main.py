from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routers import chemika as chemika_router
from app.routers import primebuild as primebuild_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="DexFlow", description="Dexterous Group automation hub")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

app.include_router(chemika_router.router, prefix="/chemika", tags=["chemika"])
app.include_router(primebuild_router.router, prefix="/primebuild", tags=["primebuild"])


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/healthz", response_class=PlainTextResponse)
async def healthz():
    return "ok"
