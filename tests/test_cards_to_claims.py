import json
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from cards_to_claims import convert, main, parse_spec  # noqa: E402


def card(n, kind="result", verdict=None):
    c = {"id": f"C{n}", "text": f"claim {n}", "kind": kind, "source": {"locator": "page 2", "page": 2, "quote": f"quote {n}", "ref": "ignored"},
         "status": "unverified", "note": "model-extracted"}
    if verdict:
        c["model_check"] = {"verdict": verdict, "why": "says more"}
    return c


def write_cards(folder, cards):
    folder.mkdir(parents=True)
    (folder / "cards.yaml").write_text(yaml.safe_dump({"claims": cards}))
    (folder / "pages").mkdir()
    (folder / "pages" / "p001.txt").write_text("text")


def test_parse_spec():
    assert parse_spec("all", 4) == [1, 2, 3, 4]
    assert parse_spec("3,7,11-13", 20) == [3, 7, 11, 12, 13]
    assert parse_spec("C2, C5", 9) == [2, 5]


def test_convert_renumbers_across_papers_and_maps_kind():
    a = {1: card(1), 2: card(2, "future_research", "overstated")}
    b = {1: card(1)}
    claims, cmap = convert([("paper-a", a, [1, 2]), ("paper-b", b, [1])])
    assert [c["id"] for c in claims] == ["C1", "C2", "C3"]
    assert [c["source"]["ref"] for c in claims] == ["paper-a", "paper-a", "paper-b"]
    assert claims[1]["kind"] == "argument" and "future_research" in claims[1]["note"] and "overstated" in claims[1]["note"]
    assert all(c["status"] == "unverified" for c in claims)
    assert cmap["C3"] == {"ref": "paper-b", "card": "C1"}


def test_reviewed_by_marks_verified_and_names_the_reader():
    claims, _ = convert([("p", {1: card(1)}, [1])], reviewed_by="A. Reader")
    assert claims[0]["status"] == "verified" and "A. Reader" in claims[0]["note"]


def test_output_validates_against_the_claim_schema(tmp_path):
    write_cards(tmp_path / "a", [card(1), card(2, "future_research")])
    out = tmp_path / "claims.yaml"
    assert main(["--from", f"paper-a={tmp_path / 'a'}:all", "-o", str(out)]) == 0
    schema = json.loads((ROOT / "schema" / "storyboard.schema.json").read_text())
    item = schema["properties"]["claims"]["items"]
    for c in yaml.safe_load(out.read_text())["claims"]:
        jsonschema.validate(c, {**item, "$defs": schema.get("$defs", {})})


def test_append_continues_numbering_and_copies_pages(tmp_path):
    write_cards(tmp_path / "a", [card(1), card(2)])
    write_cards(tmp_path / "b", [card(1)])
    out = tmp_path / "claims.yaml"
    main(["--from", f"a={tmp_path / 'a'}:1", "-o", str(out)])
    main(["--from", f"b={tmp_path / 'b'}", "-o", str(out), "--append", "--pages-root", str(tmp_path / "src")])
    ids = [c["id"] for c in yaml.safe_load(out.read_text())["claims"]]
    assert ids == ["C1", "C2"]
    assert (tmp_path / "src" / "b" / "pages" / "p001.txt").exists()
    assert set(yaml.safe_load((tmp_path / "claims-map.yaml").read_text())) == {"C1", "C2"}
