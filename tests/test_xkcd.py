import copy
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "renderers" / "xkcd"))
sys.path.insert(0, str(ROOT / "scripts"))
import render as R  # noqa: E402

EXAMPLE = ROOT / "examples" / "akam-2026-cartooning" / "storyboard.yaml"


@pytest.fixture(scope="module")
def doc():
    return yaml.safe_load(EXAMPLE.read_text())


def test_pages_are_valid_svg_with_every_panel(doc):
    svgs, _ = R.render_pages(doc)
    assert svgs
    ids = []
    for svg in svgs:
        root = ET.fromstring(svg)
        assert root.tag.endswith("svg")
        ids += re.findall(r'<g id="panel-([^"]+)"', svg)
    assert sorted(ids) == sorted(p["id"] for b in doc["beats"] for p in b["panels"])


def test_output_is_deterministic(doc):
    assert R.render_pages(doc)[0] == R.render_pages(copy.deepcopy(doc))[0]


def test_nothing_runs_past_the_bottom_margin(doc):
    _, placements = R.render_pages(doc)
    limit = R.PAGE_H - R.MARGIN - R.FOOTER_H
    assert all(p["y"] + p["h"] <= limit + 1e-6 for p in placements)


def test_the_page_fit_never_uses_more_pages_than_the_tallest_setting(doc):
    cast = {c["id"]: c for c in doc["cast"]}
    tallest = len(R.paginate(R.build_items(doc, cast, R.FIT_FACTORS[0])))
    assert len(R.render_pages(doc)[0]) <= tallest


def test_attribution_is_printed_on_the_last_page(doc):
    last = R.render_pages(doc)[0][-1]
    assert "Licence: CC BY 4.0" in last and "did not write or endorse" in last


def test_wrapped_lines_fit_their_width():
    for fs in (15, 18, 21):
        for line in R.wrap("a fairly long sentence about students drawing cartoons of biology " * 3, 300, fs):
            assert len(line) * fs * R.CHAR_W <= 300 + fs  # a single long word may overshoot by one glyph


def test_panels_without_staging_fall_back_to_scene_text(doc):
    bare = copy.deepcopy(doc)
    for b in bare["beats"]:
        for p in b["panels"]:
            p.pop("staging", None)
    svgs, _ = R.render_pages(bare)
    for svg in svgs:
        ET.fromstring(svg)
    assert "A lecture hall" in "".join(svgs)


def test_text_is_escaped(doc):
    evil = copy.deepcopy(doc)
    evil["beats"][0]["panels"][0]["scene"] = '<b>"x"</b> & more'
    svg = R.render_pages(evil)[0][0]
    ET.fromstring(svg)
    assert "<b>" not in svg


def test_every_figure_pose_and_face_draws():
    pen = R.Pen("t")
    for pose in R.ARMS:
        for face in ("neutral", "smile", "worry", "deadpan", "surprised"):
            for facing in ("left", "right"):
                svg, head = R.figure(pen, 100, 200, 1.0, pose, face, facing, "mug", {"glasses": True, "hair": "bun"})
                ET.fromstring(f"<g xmlns='http://www.w3.org/2000/svg'>{svg}</g>")
                assert head[0] == 100


def test_cli_writes_pages_and_a_sheet(tmp_path):
    assert R.main([str(EXAMPLE), "-o", str(tmp_path)]) == 0
    assert list(tmp_path.glob("page-*.svg")) and (tmp_path / "sheet.html").exists()


def _demo_doc():
    kinds = {
        "cups": {"items": [{"value": 0.3}, {"value": 1}]},
        "plot": {"series": [{"points": [[0, 0.1], [1, 0.9]], "style": "dashed"}], "notes": [{"x": 0.5, "y": 0.5, "label": "n"}], "x_label": "t", "y_label": "y"},
        "axis": {"items": [{"at": 0.1, "to": 0.4, "label": "a"}, {"at": 0.6, "label": "b", "style": "mark"}, {"at": 0.8, "label": "c"}]},
        "pie": {"items": [{"label": "a", "value": 1}, {"label": "b", "value": 2}]},
        "flow": {"items": [{"label": "a"}, {"label": "b"}]},
        "steps": {"items": [{"label": "a", "caption": "x"}, {"label": "b"}]},
        "stack": {"items": [{"label": "a", "value": 1}, {"label": "b", "value": 2, "style": "solid"}]},
        "ship": {}, "bottle": {"label": "b"}, "jar": {"label": "j"}, "flash": {"label": "f"},
        "board": {"cards": [{"label": "a"}, {"label": "b", "covered": True}]},
        "bars": {"bars": [{"label": "a", "value": 1}], "show_values": False},
    }
    props = [{"kind": k, "x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5, **spec} for k, spec in kinds.items()]
    panels = [{"id": f"B1.{i}", "scene": "s", "weight": "wide", "staging": {"props": [p], "characters": [
        {"id": "dot", "x": 0.8, "pose": "shrug", "face": "smile"}, {"id": "ines", "x": 0.9, "facing": "left"}]}}
        for i, p in enumerate(props, 1)]
    return {"version": 2, "cast": [{"id": "ines", "name": "Ines"}, {"id": "dot", "name": "Dot", "appearance": {"body": "diatom"}}],
            "meta": {"title": "T", "source": {"title": "s", "authors": ["a"], "year": 2026, "licence": "x"}},
            "beats": [{"id": "B1", "act": "result", "panels": panels}]}


def test_every_prop_kind_draws_to_valid_svg():
    svgs, _ = R.render_pages(_demo_doc())
    for svg in svgs:
        ET.fromstring(svg)
    assert len(re.findall(r'<g id="panel-', "".join(svgs))) == 13


def test_a_diatom_draws_for_every_pose_and_both_directions():
    pen = R.Pen("d")
    for pose in R.ARMS:
        for facing in ("left", "right"):
            svg, head = R.figure(pen, 100, 200, 1.0, pose, "smile", facing, "paper", {"body": "diatom"})
            ET.fromstring(f"<g xmlns='http://www.w3.org/2000/svg'>{svg}</g>")
            assert head[0] == 100 and head[1] < 200


def _page_rows(doc):
    _, placements = R.render_pages(doc)
    pages = {}
    for p in placements:
        pages.setdefault(p["page"], []).append(p)
    return pages


def test_pages_are_filled_to_the_bottom_margin(doc):
    limit = R.PAGE_H - R.MARGIN - R.FOOTER_H
    pages = _page_rows(doc)
    for n, items in pages.items():
        end = max(p["y"] + p["h"] for p in items)
        assert end <= limit + 1e-6
        if n < len(pages):  # a sparse last page may be left unstretched
            assert limit - end < 1.0


def test_rows_on_a_full_page_differ_in_height(doc):
    rows = [p["h"] for p in _page_rows(doc)[2] if p["kind"] == "row"]
    assert max(rows) / min(rows) > 1.2


def test_a_tall_hint_gives_a_row_more_height(doc):
    plain = [p["h"] for p in _page_rows(doc)[1] if p["kind"] == "row"]
    hinted = copy.deepcopy(doc)
    hinted["beats"][0]["panels"][0]["height"] = "tall"
    tall = [p["h"] for p in _page_rows(hinted)[1] if p["kind"] == "row"]
    assert tall[0] > plain[0]


def test_a_short_hint_makes_a_row_shorter(doc):
    plain = [p["h"] for p in _page_rows(doc)[1] if p["kind"] == "row"]
    hinted = copy.deepcopy(doc)
    for p in hinted["beats"][0]["panels"]:
        p["height"] = "short"
    short = [p["h"] for p in _page_rows(hinted)[1] if p["kind"] == "row"]
    assert short[0] < plain[0]


def test_a_sparse_last_page_is_not_stretched_to_fill_the_sheet(doc):
    tiny = copy.deepcopy(doc)
    tiny["beats"] = tiny["beats"][:1]
    tiny["beats"][0]["panels"] = tiny["beats"][0]["panels"][:2]
    rows = [p["h"] for p in _page_rows(tiny)[1] if p["kind"] == "row"]
    assert sum(rows) < 0.7 * (R.PAGE_H - 2 * R.MARGIN)
