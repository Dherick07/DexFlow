#!/usr/bin/env python3
"""
DexFlow automation smoke tests.

Sends real HTTP requests to the running app and compares outputs against expected files.

Prerequisites:
    pip install requests
    uvicorn app.main:app --reload   (or: docker-compose -f docker-compose.local.yml up)

Override the base URL:
    DEXFLOW_URL=http://localhost:8000 python tests/run_tests.py
"""

import os
import sys
from io import BytesIO
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("ERROR: 'requests' not installed. Run: pip install requests")

try:
    import pandas as pd
except ImportError:
    sys.exit("ERROR: 'pandas' not installed. Run: pip install pandas openpyxl")

BASE_URL = os.environ.get("DEXFLOW_URL", "http://localhost:8000")
TESTS_DIR = Path(__file__).parent
ACTUAL_DIR = TESTS_DIR / "actual"
ACTUAL_DIR.mkdir(exist_ok=True)

GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"
PASS_LABEL = f"{GREEN}PASS{RESET}"
FAIL_LABEL = f"{RED}FAIL{RESET}"

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def check_health():
    try:
        r = requests.get(f"{BASE_URL}/healthz", timeout=5)
        r.raise_for_status()
    except Exception as e:
        sys.exit(
            f"App not reachable at {BASE_URL}: {e}\n"
            "Start it first:  uvicorn app.main:app --reload"
        )


def is_html_error(r: requests.Response) -> bool:
    return "text/html" in r.headers.get("Content-Type", "")


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------

def compare_txt(actual_bytes: bytes, expected_path: Path) -> list[str]:
    actual = actual_bytes.decode("utf-8", errors="replace").splitlines()
    expected = expected_path.read_text(encoding="utf-8", errors="replace").splitlines()

    def normalize(lines):
        return [ln.rstrip() for ln in lines if ln.strip()]

    a_lines = normalize(actual)
    e_lines = normalize(expected)

    errors = []
    if len(a_lines) != len(e_lines):
        errors.append(f"  Line count: expected {len(e_lines)}, got {len(a_lines)}")

    mismatches = [
        f"  Line {i + 1}:\n    expected: {e!r}\n    actual:   {a!r}"
        for i, (a, e) in enumerate(zip(a_lines, e_lines))
        if a != e
    ]
    if mismatches:
        errors.extend(mismatches[:5])
        if len(mismatches) > 5:
            errors.append(f"  ... and {len(mismatches) - 5} more line differences")

    return errors


def _load_xlsx(data: bytes) -> dict[str, pd.DataFrame]:
    xl = pd.ExcelFile(BytesIO(data), engine="openpyxl")
    return {name: xl.parse(name) for name in xl.sheet_names}


def compare_xlsx(actual_bytes: bytes, expected_path: Path) -> list[str]:
    errors = []

    try:
        actual_sheets = _load_xlsx(actual_bytes)
    except Exception as exc:
        return [f"  Could not parse actual output as XLSX: {exc}"]

    try:
        expected_sheets = _load_xlsx(expected_path.read_bytes())
    except Exception as exc:
        return [f"  Could not parse expected file as XLSX: {exc}"]

    a_names = list(actual_sheets)
    e_names = list(expected_sheets)
    if a_names != e_names:
        errors.append(f"  Sheet names: expected {e_names}, got {a_names}")
        return errors

    for sheet in e_names:
        a_df = actual_sheets[sheet].reset_index(drop=True)
        e_df = expected_sheets[sheet].reset_index(drop=True)

        if a_df.shape != e_df.shape:
            errors.append(
                f"  [{sheet}] Shape: expected {e_df.shape}, got {a_df.shape}"
            )
            continue

        if list(a_df.columns) != list(e_df.columns):
            errors.append(
                f"  [{sheet}] Columns differ:\n"
                f"    expected: {list(e_df.columns)}\n"
                f"    actual:   {list(a_df.columns)}"
            )
            continue

        try:
            pd.testing.assert_frame_equal(
                a_df, e_df,
                check_exact=False,
                rtol=0.01,
                check_dtype=False,
                check_names=False,
                obj=f"sheet '{sheet}'",
            )
        except AssertionError as exc:
            # Trim verbose pandas output to first 10 lines
            msg = "\n".join(str(exc).splitlines()[:10])
            errors.append(f"  [{sheet}] Data mismatch:\n{msg}")

    return errors


# ---------------------------------------------------------------------------
# Single-test runner
# ---------------------------------------------------------------------------

def run_test(
    response: requests.Response,
    expected_path: Path,
    actual_stem: str,
    ext: str,
) -> bool:
    if response.status_code != 200 or is_html_error(response):
        snippet = response.text[:300].replace("\n", " ")
        print(FAIL_LABEL)
        print(f"  HTTP {response.status_code} — app returned an error:\n  {snippet}")
        return False

    actual_bytes = response.content
    actual_path = ACTUAL_DIR / f"{actual_stem}{ext}"
    actual_path.write_bytes(actual_bytes)

    errors = compare_txt(actual_bytes, expected_path) if ext == ".txt" else compare_xlsx(actual_bytes, expected_path)

    if errors:
        print(FAIL_LABEL)
        for msg in errors:
            print(msg)
        return False

    print(PASS_LABEL)
    return True


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def test_chemika_invoice_txt() -> bool:
    print("[1/4] Chemika Invoice TXT .......... ", end="", flush=True)
    input_path = TESTS_DIR / "Chemika" / "Invoice_TXT_Formatter" / "Input" / "31896 to 31904.xlsx"
    expected_path = TESTS_DIR / "Chemika" / "Invoice_TXT_Formatter" / "Output" / "31896 to 31904.txt"

    with open(input_path, "rb") as fh:
        r = requests.post(
            f"{BASE_URL}/chemika/invoice-txt",
            files={"file": (input_path.name, fh, XLSX_MIME)},
            data={
                "memo": "Certificate of Analysis",
                "account": "4-1100",
                "due_date": 2,
                "due_days": 30,
                "tax_code": "GST",
            },
        )
    return run_test(r, expected_path, "chemika_invoice_txt", ".txt")


def test_capspace_unit_register() -> bool:
    print("[2/4] Capspace Unit Register ....... ", end="", flush=True)
    input_path = (
        TESTS_DIR / "Capspace" / "Unit Register"
        / "Unit Register - Input - Capspace Statements - CPDF -  February 2026.xlsx"
    )
    expected_path = (
        TESTS_DIR / "Capspace" / "Unit Register"
        / "Unit Register - Output - Combined_Statement_Extracted.xlsx"
    )

    with open(input_path, "rb") as fh:
        r = requests.post(
            f"{BASE_URL}/capspace/unit-register",
            files={"files": (input_path.name, fh, XLSX_MIME)},
        )
    return run_test(r, expected_path, "capspace_unit_register", ".xlsx")


def test_capspace_loan_register() -> bool:
    print("[3/4] Capspace Loan Register ....... ", end="", flush=True)
    input_path = (
        TESTS_DIR / "Capspace" / "Loans Register"
        / "Loans Recon - Input - All Statements Capspace EOM FEB 26.xlsx"
    )
    expected_path = (
        TESTS_DIR / "Capspace" / "Loans Register"
        / "Loans Recon - Output -Capspace Loans Reconciliation Automation v1.6 February 2026.xlsx"
    )

    with open(input_path, "rb") as fh:
        r = requests.post(
            f"{BASE_URL}/capspace/loan-register",
            files={"file": (input_path.name, fh, XLSX_MIME)},
        )
    return run_test(r, expected_path, "capspace_loan_register", ".xlsx")


def test_capspace_interest_payments() -> bool:
    print("[4/4] Capspace Interest Payments ... ", end="", flush=True)
    input_path = (
        TESTS_DIR / "Capspace" / "Interest Payments"
        / "Interest Payments - Input - Mortgage Pool Distribution Audit Report CPDF - February 2026.xlsx"
    )
    expected_path = (
        TESTS_DIR / "Capspace" / "Interest Payments"
        / "Interest Payments - Output - Capspace_Monthly_Interest_Payments_February_2026.xlsx"
    )

    with open(input_path, "rb") as fh:
        r = requests.post(
            f"{BASE_URL}/capspace/interest-payments",
            files={"files": (input_path.name, fh, XLSX_MIME)},
        )
    return run_test(r, expected_path, "capspace_interest_payments", ".xlsx")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"DexFlow smoke tests -> {BASE_URL}\n")
    check_health()

    results = [
        test_chemika_invoice_txt(),
        test_capspace_unit_register(),
        test_capspace_loan_register(),
        test_capspace_interest_payments(),
    ]

    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} passed")
    if passed < total:
        print(f"Actual outputs saved to: {ACTUAL_DIR}")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
