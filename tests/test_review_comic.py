"""The comic review form: what it lists, and what applying its answers changes."""
import json
import re
import shutil
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import review_comic as RC  # noqa: E402

EXAMPLE = ROOT / "examples" / "southern-ocean-edna-agreement"


@pytest.fixture
def comic(tmp_path):
    dest = tmp_path / "southern-ocean-edna-agreement"
    shutil.copytree(EXAMPLE, dest, ignore=shutil.ignore_patterns("output", "*.pdf"))
    return dest


def held_jokes(folder):
    return [j["panel"] for j in RC.load_jokes(folder) if not j["confirmed"]]


def test_the_page_lists_each_held_joke_with_its_panel_drawn_and_each_unverified_claim(comic):
    ledger = comic / "claims.yaml" if (comic / "claims.yaml").exists() else sorted((comic / "claims").glob("*.yaml"))[0]
    text = ledger.read_text()
    cid = re.search(r"(?m)^- id: (C\d+)", text).group(1)
    ledger.write_text(re.sub(rf"(- id: {cid}\b.*?status:) verified", r"\1 unverified", text, count=1, flags=re.S))
    html = RC.build(comic, "southern-ocean-edna-agreement", {}, "unverified")
    assert f'id="item-claim-{cid}"' in html
    for panel in held_jokes(comic):
        assert f'id="item-joke-{panel.replace(".", "_")}"' in html
    assert "<svg" in html and "%%" not in html


def test_the_page_marks_the_quote_inside_the_page_text():
    pages = {7: "Samples were taken on the 12th of May.  Fish were then counted by eye, and only some of them were adults. The end."}
    html, found = RC.snippet(pages, 7, "Fish were then counted by eye ... only some of them were adults")
    assert found and html.count("<mark>") == 2 and "<mark>Fish were then counted by eye</mark>" in html
    assert RC.snippet(pages, 7, "words that are not there")[1] is False
    assert RC.snippet(pages, 9, "x") == ("", False)


def test_a_claim_marked_fair_becomes_verified_and_a_joke_marked_approve_is_released(comic):
    panel = held_jokes(comic)[0]
    ledger_files = RC.ledger_files(comic)
    first = yaml.safe_load(Path(ledger_files[0]).read_text())["claims"][0]["id"]
    RC.set_claim_status(comic, first, "unverified")
    answers = {f"claim-{first}": {"verdict": "keep", "checks": {"0": True, "1": True, "2": True}},
               RC.item_id("joke", panel): {"verdict": "keep", "checks": {"0": True}}}
    res = RC.apply(comic, answers)
    assert any("verified" in d for d in res["done"]) and any("approved" in d for d in res["done"])
    assert any("1 of 6 checks" in w for w in res["warnings"])  # approved, but reported: only one question ticked
    assert RC.load_ledger(comic)[first]["status"] == "verified"
    assert panel not in held_jokes(comic)


def test_rewording_and_cutting_are_a_worklist_not_an_edit(comic):
    panel = held_jokes(comic)[0]
    before = {f: Path(f).read_text() for f in RC.ledger_files(comic)}
    res = RC.apply(comic, {RC.item_id("joke", panel): {"verdict": "drop", "notes": "too cruel to the net"},
                           "claim-C001": {"verdict": "fix", "notes": "says more than the quote"},
                           "general": {"notes": "lovely"}})
    assert res["done"] == []
    assert any("cut" in t and "too cruel" in t for t in res["todo"]) and any("reword" in t for t in res["todo"])
    assert res["general"] == "lovely"
    assert panel in held_jokes(comic) and before == {f: Path(f).read_text() for f in RC.ledger_files(comic)}


def test_answers_load_from_a_plain_mapping_or_a_list_of_documents(tmp_path):
    a = tmp_path / "a.json"
    a.write_text(json.dumps({"claim-C1": {"verdict": "keep"}}))
    b = tmp_path / "b.json"
    b.write_text(json.dumps({"documents": [{"id": "claim-C1", "data": {"verdict": "keep"}}]}))
    assert RC.load_answers(a) == RC.load_answers(b) == {"claim-C1": {"verdict": "keep"}}


def test_answers_load_from_a_folder_of_one_file_per_item(tmp_path):
    (tmp_path / "review").mkdir()
    (tmp_path / "review" / "joke-B4_2.json").write_text(json.dumps({"verdict": "keep"}))
    assert RC.load_answers(tmp_path) == {"joke-B4_2": {"verdict": "keep"}}


def beat_panel(folder, pid):
    for f in sorted((folder / "beats").glob("*.yaml")):
        for beat in yaml.safe_load(f.read_text()):
            for p in beat["panels"]:
                if p["id"] == pid:
                    return p


def test_the_page_carries_the_full_comic_hidden_until_submit_and_a_change_the_picture_block_on_each_joke(comic):
    html = RC.build(comic, "southern-ocean-edna-agreement", {}, "unverified")
    assert 'id="comic" class="comic hide"' in html and html.count("<figure><svg") >= 2
    assert "Change the words, scene, characters, props or actions" in html and 'data-e="scene"' in html and 'data-line="1"' in html and "data-addprop" in html
    assert 'id="comic"' not in RC.build(comic, "southern-ocean-edna-agreement", {}, "unverified", with_comic=False)


def test_picture_changes_are_written_into_the_beat_file_and_the_storyboard_is_rebuilt(comic):
    before = beat_panel(comic, "B1.2")
    edit = {"scene": "Ines grins beside a bottle.",
            "chars": {"0": {"pose": "up", "holding": ""}},
            "props": {"0": {"label": "sea water"}},
            "add_props": [{"kind": "laptop", "label": "my notes"}],
            "add_chars": [{"id": "otto", "pose": "stand", "facing": "left"}]}
    res = RC.apply(comic, {"panel-B1_2": {"verdict": "", "edit": edit}})
    assert not res["todo"] and any("scene changed" in d for d in res["done"])
    after = beat_panel(comic, "B1.2")
    assert after["scene"] == "Ines grins beside a bottle."
    ines = after["staging"]["characters"][0]
    assert ines["pose"] == "up" and "holding" not in ines and ines["face"] == before["staging"]["characters"][0]["face"]
    assert after["staging"]["props"][0]["label"] == "sea water" and after["staging"]["props"][1] == before["staging"]["props"][1]
    assert after["staging"]["props"][-1] == {"kind": "laptop", "x": 0.55, "y": 0.3, "w": 0.3, "h": 0.45, "label": "my notes"}
    otto = after["staging"]["characters"][-1]
    assert otto["id"] == "otto" and otto["pose"] == "stand" and otto["facing"] == "left" and otto["x"] != ines["x"]
    built = yaml.safe_load((comic / "storyboard.yaml").read_text())
    assert next(p for b in built["beats"] for p in b["panels"] if p["id"] == "B1.2")["scene"] == "Ines grins beside a bottle."


def test_a_prop_can_be_removed_and_a_dry_run_writes_nothing(comic):
    path = next(f for f in (comic / "beats").glob("*.yaml") if "id: B1.2" in f.read_text())
    text = path.read_text()
    res = RC.apply(comic, {"panel-B1_2": {"edit": {"props": {"0": {"remove": True}}, "scene": "x"}}}, dry_run=True)
    assert path.read_text() == text and all("would" in d for d in res["done"])
    RC.apply(comic, {"panel-B1_2": {"edit": {"props": {"0": {"remove": True}}}}})
    assert [p["kind"] for p in beat_panel(comic, "B1.2")["staging"]["props"]] == ["sequence"]


def test_a_picture_change_that_cannot_be_written_goes_on_the_worklist(comic):
    res = RC.apply(comic, {"panel-B4_2": {"edit": {"chars": {"9": {"pose": "up"}}}}, "panel-B9_9": {"edit": {"scene": "x"}}})
    assert len(res["todo"]) == 2 and any("character 10" in t for t in res["todo"]) and any("B9" in t or "B9_9" in t for t in res["todo"])


def test_spoken_lines_can_be_retyped_removed_and_added_in_the_beat_file(comic):
    before = beat_panel(comic, "B1.2")
    assert [s["speaker"] for s in before["speech"]] == ["narrator", "ines"]
    res = RC.apply(comic, {"panel-B1_2": {"edit": {"lines": {"1": {"text": "So living things leave DNA behind."}},
                                                  "add_lines": [{"speaker": "otto", "text": "Surely not all of it."}]}}})
    after = beat_panel(comic, "B1.2")
    assert after["speech"][0] == before["speech"][0]  # the caption is untouched
    assert after["speech"][1] == {"speaker": "ines", "text": "So living things leave DNA behind."}
    assert after["speech"][2] == {"speaker": "otto", "text": "Surely not all of it."}
    assert any("now reads" in d for d in res["done"]) and not res["todo"]
    RC.apply(comic, {"panel-B1_2": {"edit": {"lines": {"2": {"remove": True}}}}})
    assert [s["speaker"] for s in beat_panel(comic, "B1.2")["speech"]] == ["narrator", "ines"]


def test_changing_a_caption_asks_for_the_claim_check_to_be_rerun(comic):
    res = RC.apply(comic, {"joke-B4_2": {"edit": {"lines": {"0": {"text": "Ten labs, ten protocols."}}}}})
    assert beat_panel(comic, "B4.2")["speech"][0]["text"] == "Ten labs, ten protocols."
    assert any("caption was changed" in t for t in res["todo"])


def test_a_joke_item_shows_its_panel_with_the_captions_covered_and_has_six_checks(comic):
    html = RC.build(comic, "southern-ocean-edna-agreement", {}, "unverified")
    item = html[html.index('id="item-joke-B4_2"'):]
    item = item[:item.index("</article>")]
    assert item.count("captions covered, as most readers see it") == 1  # the strip is one panel, so just itself
    assert item.count('data-k="') == 6 and "still lands with the captions covered" in item
    covered = [f for f in re.findall(r"<figure>.*?</figure>", item, flags=re.S) if "captions covered" in f]
    assert len(covered) == 1 and "In MZG-ICE" not in covered[0] and "####" in covered[0]  # the caption is covered by blocks, not removed


def test_each_caption_has_an_edit_caption_button_that_names_its_line(comic):
    html = RC.build(comic, "southern-ocean-edna-agreement", {}, "unverified")
    item = html[html.index('id="item-joke-B4_2"'):]
    item = item[:item.index("</article>")]
    assert item.count('data-goto-line="0"') == 1 and "Edit caption" in item  # the caption is line 0 of B4.2's speech
    assert 'data-line="0"' in item and "<b>Caption</b>" in item
