from io import BytesIO
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.automations_registry import grouped_by_client
from app.services import capspace as capspace_service

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.globals["sidebar_groups"] = grouped_by_client()

router = APIRouter()

ALLOWED_EXCEL = {".xlsx", ".xls"}
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _unit_form(request: Request, error: str | None = None, status_code: int = 200):
    return templates.TemplateResponse(
        "capspace/unit_register.html",
        {"request": request, "error": error},
        status_code=status_code,
    )


@router.get("/unit-register", response_class=HTMLResponse)
async def unit_register_form(request: Request):
    return _unit_form(request)


@router.post("/unit-register")
async def unit_register_submit(
    request: Request,
    files: List[UploadFile] = File(...),
):
    all_results = []
    for upload in files:
        filename = upload.filename or "upload.xlsx"
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXCEL:
            return _unit_form(request, f"'{filename}': expected .xlsx/.xls — got '{ext}'.", 400)
        try:
            raw = await upload.read()
            _, results = capspace_service.extract_unit_file(raw, filename)
            all_results.extend(results)
        except Exception as exc:
            return _unit_form(request, f"Couldn't process '{filename}': {exc}", 400)

    if not all_results:
        return _unit_form(request, "No investor data found. Make sure you uploaded the raw statement files.", 400)

    out_bytes = capspace_service.build_unit_excel(all_results)
    return StreamingResponse(
        BytesIO(out_bytes),
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": 'attachment; filename="Combined_Statement_Extracted.xlsx"'},
    )


def _loan_form(request: Request, error: str | None = None, status_code: int = 200):
    return templates.TemplateResponse(
        "capspace/loan_register.html",
        {"request": request, "error": error},
        status_code=status_code,
    )


@router.get("/loan-register", response_class=HTMLResponse)
async def loan_register_form(request: Request):
    return _loan_form(request)


@router.post("/loan-register")
async def loan_register_submit(
    request: Request,
    file: UploadFile = File(...),
):
    filename = file.filename or "upload.xlsx"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXCEL:
        return _loan_form(request, f"Expected .xlsx/.xls — got '{ext}'.", 400)

    try:
        raw = await file.read()
        results, detected_month = capspace_service.extract_loan_file(raw)
    except Exception as exc:
        return _loan_form(request, f"Couldn't process '{filename}': {exc}", 400)

    if not results:
        return _loan_form(request, "No borrower data found.", 400)

    out_bytes, out_name = capspace_service.build_loan_excel(results, detected_month)
    return StreamingResponse(
        BytesIO(out_bytes),
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'},
    )


def _interest_form(request: Request, error: str | None = None, status_code: int = 200):
    return templates.TemplateResponse(
        "capspace/interest_payments.html",
        {"request": request, "error": error},
        status_code=status_code,
    )


@router.get("/interest-payments", response_class=HTMLResponse)
async def interest_payments_form(request: Request):
    return _interest_form(request)


@router.post("/interest-payments")
async def interest_payments_submit(
    request: Request,
    files: List[UploadFile] = File(...),
):
    results_by_entity: dict[str, list] = {}
    month_label = ""
    for upload in files:
        filename = upload.filename or "upload.xlsx"
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXCEL:
            return _interest_form(request, f"'{filename}': expected .xlsx/.xls — got '{ext}'.", 400)
        try:
            raw = await upload.read()
            entity, ml, results = capspace_service.extract_interest_file(raw)
            if ml and not month_label:
                month_label = ml
            results_by_entity.setdefault(entity, []).extend(results)
        except Exception as exc:
            return _interest_form(request, f"Couldn't process '{filename}': {exc}", 400)

    if not results_by_entity:
        return _interest_form(request, "No investor data found. Make sure you uploaded the correct report files.", 400)

    out_bytes = capspace_service.build_interest_excel(results_by_entity, month_label)
    out_name = (
        f"Capspace_Monthly_Interest_Payments_{month_label.replace(' ', '_')}.xlsx"
        if month_label
        else "Capspace_Monthly_Interest_Payments.xlsx"
    )
    return StreamingResponse(
        BytesIO(out_bytes),
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'},
    )
