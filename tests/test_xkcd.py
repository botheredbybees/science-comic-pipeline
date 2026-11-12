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
