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
    assert "Licence: CC BY 4.0" in last and "endorse this document" in last


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
        "laptop": {"label": "l"}, "microscope": {"label": "m"}, "teapot": {"label": "t"}, "net": {"label": "n"}, "thermometer": {"label": "th"},
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
    assert len(re.findall(r'<g id="panel-', "".join(svgs))) == 18


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
            svg, head = R.figure(pen, 100, 300, 1.0, "stand", "smile", facing, None, {"hair": hair, "glasses": True})
            ET.fromstring(f"<g xmlns='http://www.w3.org/2000/svg'>{svg}</g>")
            assert head[1] <= bald[1]


def test_light_hair_is_an_outline_and_a_lab_coat_draws():
    pen = R.Pen("coat")
    dark, _ = R.figure(pen, 100, 300, 1.0, "stand", "smile", "right", None, {"hair": "bob"})
    light, _ = R.figure(pen, 100, 300, 1.0, "stand", "smile", "right", None, {"hair": "bob", "hair_tone": "light", "coat": True})
    plain, _ = R.figure(pen, 100, 300, 1.0, "stand", "smile", "right", None, {"hair": "bob", "hair_tone": "light"})
    for svg in (dark, light):
        ET.fromstring(f"<g xmlns='http://www.w3.org/2000/svg'>{svg}</g>")
    assert dark.count(f'fill="{R.INK}"') > light.count(f'fill="{R.INK}"')  # light hair has no black fill
    assert len(light) > len(plain)  # the coat adds strokes


def test_strand_hair_clipboard_and_a_mug_with_steam_draw():
    pen = R.Pen("props")
    for hair in ("bob", "long", "ponytail", "bun", "spiky"):
        svg, _ = R.figure(pen, 100, 300, 1.0, "hold", "smile", "right", "mug", {"hair": hair, "hair_tone": "strands", "coat": True})
        ET.fromstring(f"<g xmlns='http://www.w3.org/2000/svg'>{svg}</g>")
    mug = R._holding(pen, "mug", 100, 100, 1.0, 2.3)
    clip = R._holding(pen, "clipboard", 100, 100, 1.0, 2.3)
    assert mug.count("<path") >= 5  # the handle, the cup (4 edges) and three wisps of steam
    assert clip.count("<path") >= 8


def test_the_last_page_links_to_the_paper_and_its_licence(doc):
    svgs, _ = R.render_pages(doc)
    last = svgs[-1]
    ET.fromstring(last)
    assert 'href="https://doi.org/' in last or 'href="http' in last
    assert last.count("<a ") >= 3 and R.PIPELINE_URL in last and "using the " in last


def test_bar_labels_print_the_number_as_written():
    svg = R._bars(R.Pen("n"), 0, 0, 400, 300, {"unit": "%", "bars": [{"label": "a", "value": 25.0}, {"label": "b", "value": 14}, {"label": "c", "value": 11.3}]}, 16)
    assert ">25.0%<" in svg and ">14%<" in svg and ">11.3%<" in svg


def test_every_held_object_draws_in_every_pose():
    pen = R.Pen("held")
    for held in ("marker", "mug", "clipboard", "teacup", "flask", "magnifier"):
        for pose in ("stand", "hold", "think", "sip", "point", "shrug", "up"):
            svg, _ = R.figure(pen, 100, 300, 1.0, pose, "neutral", "right", held, {})
            ET.fromstring(f"<g xmlns='http://www.w3.org/2000/svg'>{svg}</g>")
            assert svg.count("<path") > 8  # the figure and something in its hand


def test_a_private_comic_is_stamped_on_every_page_and_on_the_last_page_note(doc):
    d = copy.deepcopy(doc)
    d["meta"]["private"] = True
    d["meta"]["source"]["licence"] = "All rights reserved (test)"
    svgs, _ = R.render_pages(d)
    assert all("PRIVATE: not for sharing" in s for s in svgs)
    assert "Licence terms:" not in svgs[-1]  # no Creative Commons deed to link to


def test_an_open_comic_carries_no_private_stamp(doc):
    svgs, _ = R.render_pages(doc)
    assert not any("PRIVATE" in s for s in svgs)
    assert "not under an open licence" not in svgs[-1]


def test_a_non_open_licence_without_the_flag_still_says_so(doc):
    d = copy.deepcopy(doc)
    d["meta"]["source"]["licence"] = "All rights reserved (test)"
    svgs, _ = R.render_pages(d)
    assert "not under an open licence" in svgs[-1]


def test_steps_labels_wrap_and_bottle_and_jar_keep_their_shape():
    import props as P
    pen = R.Pen(1)
    long = "Detected only by the DNA method in the paper"
    svg = P.steps(pen, 0, 0, 300, 200, {"items": [{"label": long, "caption": "c"}, {"label": "Both"}]}, 16)
    assert svg.count("<tspan") >= 5 and long not in svg  # wrapped over several lines, not one long line
    for fn in (P.bottle, P.jar):
        tall = fn(R.Pen(1), 0, 0, 300, 100, {"label": "water"}, 16)  # a wide, short box must not stretch the object
        wide = fn(R.Pen(1), 0, 0, 100, 300, {"label": "water"}, 16)
        assert tall and wide


NEW_BODIES = ["copepod", "fish", "worm", "jellyfish", "urchin", "seal", "seabird", "moss", "bacterium", "seastar", "dinoflagellate", "squid", "amphipod"]


@pytest.mark.parametrize("body", NEW_BODIES)
def test_every_new_body_draws_with_every_face_and_both_facings(body):
    from animals import ANIMALS
    assert body in ANIMALS
    for face in ("neutral", "smile", "worry", "deadpan", "surprised"):
        for facing in ("right", "left"):
            svg, head = ANIMALS[body](R.Pen(1), 200, 300, 1.0, "stand", face, facing, None, {})
            assert "<path" in svg and len(head) == 2 and head[1] < 300  # the head point is above the base


@pytest.mark.parametrize("body", NEW_BODIES)
def test_a_staged_extra_can_be_each_new_body(doc, body):
    d = copy.deepcopy(doc)
    d["beats"][0]["panels"][0].setdefault("staging", {}).setdefault("characters", []).append({"id": "extra", "x": 0.6, "body": body, "scale": 1.2})
    svgs, _ = R.render_pages(d)
    assert "<svg" in "".join(svgs)
    from validate_storyboard import validate
    assert validate(d)[0] == []  # the schema accepts the body name


SCHEMATIC_PROPS = ["sequence", "tree", "clusters", "network", "database", "filter", "tubes", "sequencer", "cpr", "echosounder", "venn",
                   "satellite", "radar", "radarscreen", "icecore", "massspec", "helicopter", "drone", "aquarium", "freezer", "tag", "scatter", "boxplot", "modelgrid", "ship", "ctd", "bongo", "trawl", "rmt", "net",
                   "stake", "emsled", "fieldcamp", "molecule", "map", "currents", "iceberg", "iceshelf", "seaice", "mixedlayer"]


@pytest.mark.parametrize("kind", SCHEMATIC_PROPS)
def test_every_schematic_prop_draws_inside_its_box_in_a_wide_and_a_tall_box(kind):
    import props as P
    spec = {"kind": kind, "label": "label", "items": [{"label": "a"}, {"label": "b"}, {"label": "c"}]}
    for w, h in ((300, 100), (100, 300), (200, 200)):
        svg = P.extra_prop(R.Pen(1), 50, 50, w, h, spec, 16)
        assert "<" in svg
        ys = [float(v) for v in re.findall(r'(?<![a-z])(?:cy|y|y1|y2)="(-?[\d.]+)"', svg)]
        assert not ys or (min(ys) >= 50 - 25 and max(ys) <= 50 + h + 25), (kind, w, h, min(ys), max(ys))


@pytest.mark.parametrize("kind", SCHEMATIC_PROPS)
def test_a_schematic_prop_is_accepted_by_the_schema_and_renders_in_a_panel(doc, kind):
    from validate_storyboard import validate
    d = copy.deepcopy(doc)
    d["beats"][0]["panels"][0].setdefault("staging", {}).setdefault("props", []).append({"kind": kind, "x": 0.6, "y": 0.2, "w": 0.3, "h": 0.5})
    assert validate(d)[0] == []
    assert "<svg" in "".join(R.render_pages(d)[0])


def test_the_validator_knows_the_new_objects_when_a_scene_names_them(doc):
    from validate_storyboard import validate
    d = copy.deepcopy(doc)
    d["beats"][0]["panels"][0]["scene"] = "A sequencer stands next to a database."
    _, warnings = validate(d)
    assert any("mentions a sequencer" in w for w in warnings) and any("mentions a database" in w for w in warnings)


@pytest.mark.parametrize("outfit", ["floatcoat", "parka", "hivis"])
def test_each_outfit_and_the_hard_hat_draw_in_every_pose_in_the_palette_only(outfit):
    import draw
    palette = {draw.INK, draw.PAPER, draw.SOFT, draw.MID, "none"}
    for pose in ("stand", "point", "hold", "think", "shrug", "sip", "up"):
        svg, head = R.figure(R.Pen(1), 200, 300, 1.0, pose, "smile", "right", "clipboard", {"outfit": outfit, "hair": "hardhat"})
        assert "<path" in svg and head[1] < 300
        colours = set(re.findall(r'(?:fill|stroke)="(#[0-9a-fA-F]{3,6}|[a-z]+)"', svg))
        assert colours <= palette, colours - palette  # black, white and grey only


def test_a_map_pins_places_and_a_wide_map_includes_australia():
    import props as P
    spec = {"kind": "map", "view": "wide", "places": [{"lon": 147.3, "lat": -42.9, "label": "Hobart"}]}
    wide = P.extra_prop(R.Pen(1), 0, 0, 300, 300, spec, 16)
    polar = P.extra_prop(R.Pen(1), 0, 0, 300, 300, {"kind": "map"}, 16)
    assert "Hobart" in wide
    assert wide.count("<path") > polar.count("<path")  # more land outlines in the wide view than in the polar cap


def test_a_map_and_its_currents_share_one_geometry():
    """Currents laid over a map must line up with it: both place the pole at the same point for the same box and view."""
    import props as P
    for view in ("polar", "wide"):
        box = (10, 20, 300, 300)
        edge, x, y, w, h, lines, fsb, cx, cy, R = P._map_frame(*box, {"view": view}, 16)
        assert (cx, cy) == (x + w / 2, y + h / 2) and R == min(w, h) / 2
        assert P._polar(0, -90, cx, cy, R, edge) == (cx, cy)  # the pole is the centre


@pytest.mark.parametrize("cond", ["pancake", "pack", "drift", "fast"])
def test_each_sea_ice_condition_draws(cond):
    import props as P
    assert P.extra_prop(R.Pen(1), 0, 0, 300, 200, {"kind": "seaice", "condition": cond}, 16)
