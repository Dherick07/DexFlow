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
