import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _tracked_files() -> list[str]:
    output = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    return output.splitlines()


def _tracked_existing_files() -> list[str]:
    return [name for name in _tracked_files() if (ROOT / name).exists()]


def test_python_uses_canonical_scraper_namespace_only():
    offenders: list[str] = []
    for name in _tracked_existing_files():
        if not name.endswith(".py"):
            continue
        if name == "tests/test_td016_legacy_surface_retirement.py":
            continue
        source = (ROOT / name).read_text(encoding="utf-8")
        if "src" + ".scrapers" in source:
            offenders.append(name)

    assert offenders == []


def test_legacy_scrapers_package_is_retired():
    legacy_files = [
        name for name in _tracked_existing_files() if name.startswith("src/scrapers/")
    ]

    assert not (ROOT / "src" / "scrapers").exists()
    assert legacy_files == []


def test_dead_frontend_interpret_quote_adapter_is_retired():
    tracked = set(_tracked_existing_files())

    assert not (
        ROOT / "frontend" / "src" / "features" / "decision" / "interpret-quote.ts"
    ).exists()
    assert "frontend/src/features/decision/interpret-quote.ts" not in tracked

    offenders = []
    for name in tracked:
        if not name.startswith("frontend/src/"):
            continue
        if not (name.endswith(".ts") or name.endswith(".tsx")):
            continue
        source = (ROOT / name).read_text(encoding="utf-8")
        if "interpretQuoteForReview" in source or "createDecisionReadout" in source:
            offenders.append(name)

    assert offenders == []


def test_support_quote_fixture_remains_explicit_demo_input_only():
    consumers = []
    for name in _tracked_existing_files():
        if not name.startswith("frontend/src/"):
            continue
        if not (name.endswith(".ts") or name.endswith(".tsx")):
            continue
        source = (ROOT / name).read_text(encoding="utf-8")
        if "features/decision/fixtures/support-quote" in source:
            consumers.append(name)

    assert sorted(consumers) == [
        "frontend/src/features/decision/components/DecisionReviewFlow.tsx",
        "frontend/src/features/decision/components/DecisionReviewPage.tsx",
    ]
