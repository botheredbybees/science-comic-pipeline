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


def _rows(doc):
    cast = {c["id"]: c for c in doc["cast"]}
    return [it for it in R.build_items(doc, cast) if it["kind"] == "row"]


def test_no_two_adjacent_rows_have_identical_widths(doc):
    rows = _rows(doc)
    assert all(a["widths"] != b["widths"] for a, b in zip(rows, rows[1:]))


def test_two_all_open_rows_never_sit_together():
    base = yaml.safe_load(EXAMPLE.read_text())
    for beat in base["beats"]:  # make every panel open, then the renderer must outline some
        for p in beat["panels"]:
            p["frame"] = "borderless"
    rows = _rows(base)
    assert not any(a["all_open"] and b["all_open"] for a, b in zip(rows, rows[1:]))


def test_the_original_document_is_not_changed_by_the_frame_rule():
    base = yaml.safe_load(EXAMPLE.read_text())
    for beat in base["beats"]:
        for p in beat["panels"]:
            p["frame"] = "borderless"
    R.render_pages(base)
    assert all(p["frame"] == "borderless" for beat in base["beats"] for p in beat["panels"])


def test_a_long_chart_label_is_never_cut_short():
    from props import extra_prop
    pen = R.Pen("t")
    label = "top 20 OTUs: 78 percent of all sequence reads in the survey"
    svg = extra_prop(pen, 0, 0, 120, 200, {"kind": "pie", "items": [{"label": label, "value": 3}, {"label": "rest", "value": 1}]}, 18)
    words = re.sub(r"<[^>]+>", " ", svg).split()
    for word in label.split():
        assert word in words


def test_every_animal_draws_for_every_face_pose_and_direction():
    from animals import ANIMALS
    pen = R.Pen("animals")
    for name in ANIMALS:
        for face in ("neutral", "smile", "worry", "deadpan", "surprised"):
            for facing in ("left", "right"):
                for pose in ("stand", "up", "shrug"):
                    svg, head = R.figure(pen, 100, 200, 1.0, pose, face, facing, None, {"body": name})
                    ET.fromstring(f"<g xmlns='http://www.w3.org/2000/svg'>{svg}</g>")
                    assert head[1] < 200 and abs(head[0] - 100) < 80


def test_animals_work_as_cast_members_in_a_panel(doc):
    animal_doc = copy.deepcopy(doc)
    animal_doc["cast"] += [{"id": "krill", "name": "Krill", "appearance": {"body": "krill"}},
                           {"id": "penguin", "name": "Penguin", "appearance": {"body": "penguin"}},
                           {"id": "whale", "name": "Whale", "appearance": {"body": "whale"}}]
    panel = animal_doc["beats"][0]["panels"][0]
    panel["staging"]["characters"] += [{"id": "krill", "x": 0.2, "scale": 1.6}, {"id": "penguin", "x": 0.5, "face": "smile"},
                                      {"id": "whale", "x": 0.85, "scale": 0.6, "facing": "left"}]
    panel["speech"].append({"speaker": "whale", "text": "Hello."})
    from validate_storyboard import validate
    assert validate(animal_doc)[0] == []
    for svg in R.render_pages(animal_doc)[0]:
        ET.fromstring(svg)


def test_board_card_labels_shrink_to_fit_their_cards():
    pen = R.Pen("board")
    spec = {"kind": "board", "cards": [{"label": "diazotrophs"}, {"label": "pico"}, {"label": "calcifiers"}, {"label": "silicifiers"}]}
    svg = R.prop(pen, 0, 0, 220, 120, spec, {}, 18)
    sizes = [float(m) for m in re.findall(r'font-size="([\d.]+)"', svg)]
    assert sizes and min(sizes) < 18 and min(sizes) >= 9


def test_bars_draw_a_title_and_hang_negative_values_below_zero():
    pen = R.Pen("b")
    spec = {"title": "Selectivity", "min": -1, "max": 1, "bars": [{"label": "a", "value": 0.5}, {"label": "b", "value": -0.5}]}
    svg = R._bars(pen, 0, 0, 400, 300, spec, 16)
    ET.fromstring(f"<svg xmlns='http://www.w3.org/2000/svg'>{svg}</svg>")
    assert "Selectivity" in svg and "-0.5" in svg and ">-1<" in svg.replace(" ", "")
    # the positive value label sits above the negative one
    ys = {m.group(2): float(m.group(1)) for m in re.finditer(r'y="([\d.]+)"[^>]*><tspan[^>]*>(-?0\.5)<', svg)}
    assert ys["0.5"] < ys["-0.5"]


def test_an_extra_can_be_an_animal_by_naming_a_body_in_the_staging(doc):
    d = copy.deepcopy(doc)
    d["beats"][0]["panels"][0]["staging"]["characters"] += [{"id": "extra", "x": 0.6, "body": "salp", "scale": 1.2}]
    from validate_storyboard import validate
    import jsonschema
    assert validate(d)[0] == []
    with_salp = "".join(R.render_pages(d)[0])
    plain = "".join(R.render_pages(doc)[0])
    assert with_salp != plain and "<svg" in with_salp


def test_the_colophon_names_the_licence_deed():
    assert R._licence_url("CC BY 4.0") == "https://creativecommons.org/licenses/by/4.0/"
    assert R._licence_url("CC BY-SA 4.0") == "https://creativecommons.org/licenses/by-sa/4.0/"
    assert R._licence_url("All rights reserved") == ""


def test_every_hair_style_draws_over_the_head_and_raises_the_head_point():
    pen = R.Pen("hair")
    _, bald = R.figure(pen, 100, 300, 1.0, "stand", "smile", "right", None, {})
    for hair in ("bob", "long", "ponytail", "bun", "spiky", "beanie"):
        for facing in ("left", "right"):
            svg, head = R.figure(pen, 100, 300, 1.0, "stand", "smile", facing, None, {"hair": hair, "glasses": True, "lanyard": True})
            ET.fromstring(f"<g xmlns='http://www.w3.org/2000/svg'>{svg}</g>")
            assert head[1] <= bald[1]
