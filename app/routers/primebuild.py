import io
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.services import primebuild as primebuild_service

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

router = APIRouter()

ALLOWED_XLSX = {".xlsx"}
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
ZIP_MEDIA_TYPE = "application/zip"


def _journals_form(request: Request, error: str | None = None, status_code: int = 200):
    return templates.TemplateResponse(
        "primebuild/journals.html",
        {"request": request, "error": error},
        status_code=status_code,
    )


@router.get("/journals", response_class=HTMLResponse)
async def journals_form(request: Request):
    return _journals_form(request)


@router.post("/journals")
async def journals_submit(
    request: Request,
    files: List[UploadFile] = File(...),
    payment_date: str = Form(...),
):
    try:
        dt = datetime.strptime(payment_date, "%Y-%m-%d")
    except ValueError:
        return _journals_form(request, f"Invalid payment date '{payment_date}'.", 400)
    pdate_str = dt.strftime("%d/%m/%Y")

    output_files: dict[str, bytes] = {}
    for upload in files:
        filename = upload.filename or "upload.xlsx"
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_XLSX:
            return _journals_form(request, f"'{filename}': expected .xlsx — got '{ext}'.", 400)
        try:
            raw = await upload.read()
            rows, out_name, state, freq, cwi = primebuild_service.process_raw_file(
                raw, filename, pdate_str
            )
            output_files[out_name] = primebuild_service.build_journal_workbook(
                rows, state, freq, cwi, pdate_str
            )
        except Exception as exc:
            return _journals_form(request, f"Couldn't process '{filename}': {exc}", 400)

    if not output_files:
        return _journals_form(request, "No journal files generated.", 400)

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, fbytes in output_files.items():
            zf.writestr(fname, fbytes)
    zip_buf.seek(0)
    zip_name = f"Payroll_Journals_{dt.strftime('%Y%m%d')}.zip"
    return StreamingResponse(
        zip_buf,
        media_type=ZIP_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{zip_name}"'},
    )


def _hours_form(request: Request, error: str | None = None, status_code: int = 200):
    return templates.TemplateResponse(
        "primebuild/hours_worked.html",
        {"request": request, "error": error},
        status_code=status_code,
    )


@router.get("/hours-worked", response_class=HTMLResponse)
async def hours_worked_form(request: Request):
    return _hours_form(request)


@router.post("/hours-worked")
async def hours_worked_submit(
    request: Request,
    files: List[UploadFile] = File(...),
):
    outputs: list[tuple[str, bytes]] = []
    for upload in files:
        filename = upload.filename or "upload.xlsx"
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_XLSX:
            return _hours_form(request, f"'{filename}': expected .xlsx — got '{ext}'.", 400)
        try:
            raw = await upload.read()
            result = primebuild_service.process_hours_file(raw, filename)
            if "error" in result:
                return _hours_form(request, f"'{filename}': {result['error']}", 400)
            xlsx_bytes = primebuild_service.build_hours_excel(result)
        except Exception as exc:
            return _hours_form(request, f"Couldn't process '{filename}': {exc}", 400)
        outputs.append((f"Compliance_{result['filename_stem']}.xlsx", xlsx_bytes))

    if not outputs:
        return _hours_form(request, "Upload at least one timesheet (.xlsx).", 400)

    if len(outputs) == 1:
        out_name, out_bytes = outputs[0]
        return StreamingResponse(
            BytesIO(out_bytes),
            media_type=XLSX_MEDIA_TYPE,
            headers={"Content-Disposition": f'attachment; filename="{out_name}"'},
        )

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in outputs:
            zf.writestr(name, data)
    zip_buf.seek(0)
    zip_name = f"PrimebuildCompliance_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip"
    return StreamingResponse(
        zip_buf,
        media_type=ZIP_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{zip_name}"'},
    )


def _keypay_form(request: Request, error: str | None = None, status_code: int = 200):
    default_name = "Unapproved and Unallocated Timesheets"
    return templates.TemplateResponse(
        "primebuild/keypay_location.html",
        {"request": request, "error": error, "default_name": default_name},
        status_code=status_code,
    )


@router.get("/keypay-location", response_class=HTMLResponse)
async def keypay_location_form(request: Request):
    return _keypay_form(request)


@router.post("/keypay-location")
async def keypay_location_submit(
    request: Request,
    file: UploadFile = File(...),
    custom_name: str = Form("Unapproved and Unallocated Timesheets"),
):
    filename = file.filename or "upload.xlsx"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_XLSX:
        return _keypay_form(request, f"Expected .xlsx — got '{ext}'.", 400)

    try:
        raw = await file.read()
        df_raw = pd.read_excel(BytesIO(raw), sheet_name="All Timesheets").dropna(how="all")
    except Exception as exc:
        return _keypay_form(request, f"Couldn't read '{filename}': {exc}", 400)

    try:
        results = primebuild_service.kl_classify_all(df_raw)
        out_bytes = primebuild_service.kl_build_excel(df_raw, results)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Processing error: {exc}")

    today_prefix = datetime.now().strftime("%Y%m%d")
    stem = custom_name.strip() or "Unapproved and Unallocated Timesheets"
    out_name = f"{today_prefix}_{stem}.xlsx"
    return StreamingResponse(
        BytesIO(out_bytes),
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'},
    )
