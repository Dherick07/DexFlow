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
