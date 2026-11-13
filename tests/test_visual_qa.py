import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from export_pdf import find_browser  # noqa: E402
from visual_qa import scan  # noqa: E402

pytestmark = pytest.mark.skipif(find_browser() is None, reason="needs Chrome or Chromium")
EXAMPLE = ROOT / "examples" / "akam-2026-cartooning" / "storyboard.yaml"


def test_a_clean_example_has_no_defects():
    res = scan(EXAMPLE)
    assert len(res["pages"]) == 2 and sum(p["panels"] for p in res["pages"]) == 11
    assert res["overflow"] == [] and res["overlap"] == [] and res["clipped"] == []


def test_overlapping_text_is_reported(tmp_path):
    import yaml
    doc = yaml.safe_load(EXAMPLE.read_text())
    panel = doc["beats"][0]["panels"][0]
    # two captions drawn at the same place
    panel.setdefault("staging", {}).setdefault("props", []).extend(
        [{"kind": "label", "x": 0.5, "y": 0.5, "label": "same spot"}, {"kind": "label", "x": 0.5, "y": 0.5, "label": "same spot too"}])
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump(doc))
    res = scan(bad)
    assert any("same spot" in d["text"] or "same spot" in d["other"] for d in res["overlap"])


def test_a_relative_keep_folder_works(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    res = scan(EXAMPLE, keep="kept")
    assert res["overflow"] == [] and (tmp_path / "kept" / "page-1.svg").exists()


def test_text_cut_off_by_its_own_panel_is_reported(tmp_path):
    import yaml
    doc = yaml.safe_load(EXAMPLE.read_text())
    panel = doc["beats"][0]["panels"][0]
    panel.setdefault("staging", {}).setdefault("props", []).append(
        {"kind": "label", "x": 0.72, "y": 0.5, "label": "approximately 1 m from the bottom of the core"})
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump(doc))
    res = scan(bad)
    assert any("approximately" in d["text"] for d in res["clipped"])
    assert scan(EXAMPLE)["clipped"] == []
