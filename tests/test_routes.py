from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_landing_route_returns_landing_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "Your accounting" in r.text
    assert "all in one place" in r.text
    assert "Sign in with Microsoft" in r.text


def test_home_route_shows_featured_four():
    r = client.get("/home")
    assert r.status_code == 200
    # Four featured cards — check each expected name renders
    for name in ("Unit Register", "Invoice TXT Formatter", "Payroll Journals", "Keypay Location"):
        assert name in r.text


def test_home_route_includes_sidebar():
    r = client.get("/home")
    assert r.status_code == 200
    assert "Dexterous automation hub" in r.text
    # Sidebar chips for each client
    assert "Capspace" in r.text
    assert "Chemika" in r.text
    assert "Primebuild" in r.text


def test_automations_route_lists_all_eight():
    r = client.get("/automations")
    assert r.status_code == 200
    # Subtitle wording pins the count
    assert "All 8 automations" in r.text
    # Every automation name appears in the grid
    for name in (
        "Unit Register", "Loan Register", "Interest Payments",
        "Payroll Timesheet Extractor", "Invoice TXT Formatter",
        "Payroll Journals", "Hours Worked", "Keypay Location",
    ):
        assert name in r.text


def test_healthz_still_works():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.text == "ok"
