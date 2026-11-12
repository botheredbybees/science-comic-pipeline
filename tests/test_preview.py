import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from preview_storyboard import build  # noqa: E402

EXAMPLE = ROOT / "examples" / "akam-2026-cartooning" / "storyboard.yaml"


def _doc():
    return yaml.safe_load(EXAMPLE.read_text())


def test_every_panel_and_claim_appears_once():
    doc = _doc()
    html = build(doc)
    for beat in doc["beats"]:
        for p in beat["panels"]:
            assert html.count(f'id="panel-{p["id"]}"') == 1
    for c in doc["claims"]:
        assert html.count(f'id="claim-{c["id"]}"') == 1


def test_every_claim_chip_points_at_an_existing_claim():
    import re
    html = build(_doc())
    for target in set(re.findall(r'href="#claim-(C\d+)"', html)):
        assert f'id="claim-{target}"' in html


def test_text_is_escaped():
    doc = _doc()
    doc["beats"][0]["panels"][0]["scene"] = "<script>alert(1)</script> & more"
    html = build(doc)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt; &amp; more" in html


def test_left_out_section_renders_only_when_present():
    doc = _doc()
    assert "Left out of this draft" in build(doc)
    del doc["meta"]["left_out"]
    assert "Left out of this draft" not in build(doc)


def test_standalone_wraps_in_a_document():
    assert build(_doc(), standalone=True).startswith("<!doctype html>")
    assert not build(_doc()).startswith("<!doctype")


def test_weight_sets_panel_units_and_all_layouts_are_offered():
    html = build(_doc())
    assert 'style="--u:3"' in html and 'style="--u:1"' in html and 'style="--u:4"' in html
    for layout in ("strip", "rows", "stack"):
        assert f'data-set-layout="{layout}"' in html


def test_transition_and_word_picture_are_shown():
    html = build(_doc())
    assert "from previous: scene-to-scene" in html
    assert "words and picture: interdependent" in html
