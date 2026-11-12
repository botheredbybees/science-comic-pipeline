import copy
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from validate_storyboard import main, validate  # noqa: E402

EXAMPLE = ROOT / "examples" / "akam-2026-cartooning" / "storyboard.yaml"


@pytest.fixture
def doc():
    return yaml.safe_load(EXAMPLE.read_text())


def test_example_has_no_errors(doc):
    errors, _ = validate(doc)
    assert errors == []


def test_example_is_fully_verified_and_clean(doc):
    errors, warnings = validate(doc)
    assert errors == [] and warnings == []


def test_abstract_only_claim_drawn_in_a_panel_is_a_warning(doc):
    doc["claims"][0]["status"] = "abstract_only"
    _, warnings = validate(doc)
    assert any("C1 is abstract_only" in w for w in warnings)


def test_unknown_speaker_is_an_error(doc):
    doc["pages"][0]["panels"][0]["speech"][0]["speaker"] = "nobody"
    errors, _ = validate(doc)
    assert any("'nobody' is not in the cast" in e for e in errors)


def test_unknown_claim_is_an_error(doc):
    doc["pages"][0]["panels"][0]["claim_ids"] = ["C99"]
    errors, _ = validate(doc)
    assert any("unknown claim C99" in e for e in errors)


def test_number_without_claim_is_an_error(doc):
    panel = doc["pages"][0]["panels"][0]
    panel["claim_ids"] = []
    panel["speech"] = [{"speaker": "narrator", "text": "Seventy-nine, no, 79 students."}]
    errors, _ = validate(doc)
    assert any("contains a number but the panel cites no claim" in e for e in errors)


def test_unused_claim_is_a_warning(doc):
    doc["claims"].append(
        {"id": "C98", "text": "Spare.", "kind": "background", "source": {"locator": "abstract"}, "status": "verified"}
    )
    errors, warnings = validate(doc)
    assert errors == []
    assert any("C98 is in the ledger but no panel uses it" in w for w in warnings)


def test_joke_on_cited_panel_is_a_warning_until_reviewed(doc):
    panel = doc["pages"][0]["panels"][0]
    panel["claim_ids"] = ["C1"]
    panel["humour"] = {"note": "deadpan"}
    _, warnings = validate(doc)
    assert any("joke on a panel that cites C1" in w for w in warnings)
    panel["humour"]["keeps_claims_intact"] = True
    _, warnings = validate(doc)
    assert not any("joke on a panel that cites C1" in w for w in warnings)


def test_duplicate_ids_are_errors(doc):
    doc["cast"].append(copy.deepcopy(doc["cast"][0]))
    errors, _ = validate(doc)
    assert any("duplicate cast id" in e for e in errors)


def test_schema_error_stops_other_checks(doc):
    del doc["meta"]["spine"]
    errors, _ = validate(doc)
    assert errors and all(e.startswith("schema:") for e in errors)


def test_cli_exit_codes(tmp_path, capsys):
    assert main([str(EXAMPLE)]) == 0
    assert main([str(EXAMPLE), "--strict"]) == 0  # the example is clean
    warned = yaml.safe_load(EXAMPLE.read_text())
    warned["claims"][0]["status"] = "unverified"
    path = tmp_path / "warned.yaml"
    path.write_text(yaml.safe_dump(warned))
    assert main([str(path)]) == 0
    assert main([str(path), "--strict"]) == 1
    bad = tmp_path / "bad.yaml"
    bad.write_text("version: 1\n")
    assert main([str(bad)]) == 1
