from app.automations_registry import (
    AUTOMATIONS,
    Automation,
    featured,
    grouped_by_client,
)


def test_registry_has_all_eight_ported_automations():
    assert len(AUTOMATIONS) == 8


def test_every_automation_has_required_fields():
    for a in AUTOMATIONS:
        assert a.slug and isinstance(a.slug, str)
        assert a.name and isinstance(a.name, str)
        assert a.client in {"capspace", "chemika", "primebuild"}
        assert a.client_hue in {"sky", "mint", "lavender", "peach", "butter"}
        assert a.href.startswith("/")
        assert a.icon and isinstance(a.icon, str)


def test_slugs_are_unique():
    slugs = [a.slug for a in AUTOMATIONS]
    assert len(slugs) == len(set(slugs))


def test_featured_returns_only_featured_entries():
    assert all(a.featured for a in featured())
    assert len(featured()) == 4


def test_featured_ids_match_spec():
    names = {a.name for a in featured()}
    assert names == {
        "Unit Register",
        "Invoice TXT Formatter",
        "Payroll Journals",
        "Keypay Location",
    }


def test_grouped_by_client_preserves_expected_clients():
    groups = grouped_by_client()
    assert set(groups.keys()) == {"capspace", "chemika", "primebuild"}
    assert len(groups["capspace"]) == 3
    assert len(groups["chemika"]) == 2
    assert len(groups["primebuild"]) == 3


def test_grouped_by_client_preserves_registry_order():
    """Within a group, automations appear in the same order they're declared in AUTOMATIONS."""
    groups = grouped_by_client()
    capspace_slugs = [a.slug for a in groups["capspace"]]
    # Declared order must be: unit-register, loan-register, interest-payments.
    assert capspace_slugs == ["unit-register", "loan-register", "interest-payments"]
