"""Single source of truth for all DexFlow automations.

The home featured grid, /automations listing, and sidebar nav all iterate
this list. Adding a new automation = one entry here + a router + a template.
"""
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Automation:
    slug: str              # URL segment within its client prefix, e.g. "unit-register"
    name: str              # Display name, e.g. "Unit Register"
    client: str            # Client slug: "capspace" | "chemika" | "primebuild"
    client_label: str      # Display label for the chip, e.g. "Capspace"
    client_hue: str        # Tile/chip colour modifier: sky | mint | lavender | peach | butter
    description: str       # One-line card description
    icon: str              # Icon name resolved by _icons.html macro
    href: str              # Full route path, e.g. "/capspace/unit-register"
    featured: bool = False


AUTOMATIONS: List[Automation] = [
    Automation(
        slug="unit-register",
        name="Unit Register",
        client="capspace",
        client_label="Capspace",
        client_hue="sky",
        description="Combine CPDF / DLOT / CDLOT2 investor statements into a single Client Statement workbook.",
        icon="table-cells",
        href="/capspace/unit-register",
        featured=True,
    ),
    Automation(
        slug="loan-register",
        name="Loan Register",
        client="capspace",
        client_label="Capspace",
        client_hue="sky",
        description="Extract Entity, Borrower, Balance, Interest, Reserve from the monthly Capspace Loans statement.",
        icon="document-text",
        href="/capspace/loan-register",
    ),
    Automation(
        slug="interest-payments",
        name="Interest Payments",
        client="capspace",
        client_label="Capspace",
        client_hue="sky",
        description="Consolidate Mortgage Pool Distribution Audit Reports into per-entity sheets with Payee flags.",
        icon="banknotes",
        href="/capspace/interest-payments",
    ),
    Automation(
        slug="payroll-extractor",
        name="Payroll Timesheet Extractor",
        client="chemika",
        client_label="Chemika",
        client_hue="mint",
        description="Consolidate employee timesheet .xlsx files into a single monthly payroll summary.",
        icon="clock",
        href="/chemika/payroll-extractor",
    ),
    Automation(
        slug="invoice-txt",
        name="Invoice TXT Formatter",
        client="chemika",
        client_label="Chemika",
        client_hue="mint",
        description="Convert invoice spreadsheet into tab-delimited .txt for accounting import.",
        icon="document-arrow-down",
        href="/chemika/invoice-txt",
        featured=True,
    ),
    Automation(
        slug="journals",
        name="Payroll Journals",
        client="primebuild",
        client_label="Primebuild",
        client_hue="lavender",
        description="Convert raw JNL exports into formatted General Ledger Journal Download files, bundled as a ZIP.",
        icon="book-open",
        href="/primebuild/journals",
        featured=True,
    ),
    Automation(
        slug="hours-worked",
        name="Hours Worked — Compliance",
        client="primebuild",
        client_label="Primebuild",
        client_hue="lavender",
        description="Flag long shifts, short breaks, fatigue risk, and >60h/week from timesheet exports.",
        icon="shield-check",
        href="/primebuild/hours-worked",
    ),
    Automation(
        slug="keypay-location",
        name="Keypay Location",
        client="primebuild",
        client_label="Primebuild",
        client_hue="lavender",
        description="Classify Keypay timesheets into approved / unapproved × allocated / unallocated categories.",
        icon="map-pin",
        href="/primebuild/keypay-location",
        featured=True,
    ),
]


def featured() -> List[Automation]:
    """Return automations flagged featured=True, preserving registry order."""
    return [a for a in AUTOMATIONS if a.featured]


def grouped_by_client() -> Dict[str, List[Automation]]:
    """Group automations by client slug, preserving within-group registry order.

    Returns a dict in client-appearance order (as of today: capspace, chemika,
    primebuild). Python 3.7+ dict preserves insertion order, so iteration order
    is stable.
    """
    groups: Dict[str, List[Automation]] = {}
    for a in AUTOMATIONS:
        groups.setdefault(a.client, []).append(a)
    return groups
