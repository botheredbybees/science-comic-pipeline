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
import faces as F  # noqa: E402

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
        for face in F.ALL:
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


def test_light_hair_clipboard_and_a_mug_with_steam_draw():
    pen = R.Pen("props")
    for hair in ("bob", "long", "ponytail", "bun", "spiky"):
        svg, _ = R.figure(pen, 100, 300, 1.0, "hold", "smile", "right", "mug", {"hair": hair, "hair_tone": "light", "coat": True})
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
    for held in ("marker", "mug", "clipboard", "teacup", "flask", "magnifier", "flower", "photo", "book", "paper"):
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


NEW_BODIES = ["copepod", "fish", "worm", "jellyfish", "urchin", "seal", "seabird", "moss", "bacterium", "seastar", "dinoflagellate", "squid", "amphipod", "puppet"]


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
                   "stake", "emsled", "fieldcamp", "molecule", "map", "currents", "iceberg", "iceshelf", "seaice", "mixedlayer", "clay", "mosaic", "armchair", "wheelchair", "piano", "guitar", "easel", "camera", "brain", "headphones", "notes",
                   "gallery", "cycle", "book", "headprofile", "cloud", "scales", "door", "heart", "trolley", "van", "skyline", "staff", "livingroom", "gears", "ear", "funnel",
                   "stage", "blackbox", "circle", "hospitalroom", "bridge", "eye", "bookshelf", "spinalcord"]


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


def test_a_figure_can_be_enlarged_and_cropped_by_the_panels_edge(doc):
    """x beyond 0 or 1, y beyond 1 and a large scale are accepted: the panel clips what sticks out."""
    from validate_storyboard import validate
    d = copy.deepcopy(doc)
    panel = d["beats"][0]["panels"][0]
    panel.setdefault("staging", {})["characters"] = [{"id": "extra", "body": "whale", "x": -0.3, "y": 0.9, "scale": 3.0},
                                                      {"id": "extra", "body": "krill", "x": 1.2, "y": 1.6, "scale": 7.0}]
    assert validate(d)[0] == []
    svgs, _ = R.render_pages(d)
    assert 'clip-path="url(#clip-B1-1)"' in "".join(svgs)  # what overflows is clipped by the panel
    panel["staging"]["characters"][0]["scale"] = 9.0
    assert validate(d)[0]  # beyond the limit is refused


def test_a_prop_marked_front_is_drawn_after_the_characters(doc):
    d = copy.deepcopy(doc)
    st = d["beats"][0]["panels"][0].setdefault("staging", {})
    st["characters"] = [{"id": "extra", "body": "krill", "x": 0.5}]
    st["props"] = [{"kind": "label", "x": 0.5, "y": 0.5, "label": "FRONTMARK"}]
    behind = "".join(R.render_pages(d)[0])
    st["props"][0]["front"] = True
    in_front = "".join(R.render_pages(d)[0])
    assert in_front.index("FRONTMARK") > behind.index("FRONTMARK")  # drawn later, so on top


def test_a_box_grows_to_hold_a_long_label_and_there_is_no_sign_prop(doc):
    import validate_storyboard as V
    d = copy.deepcopy(doc)
    panel = d["beats"][0]["panels"][0]
    panel["staging"] = {"props": [{"kind": "box", "x": 0.1, "y": 0.1, "w": 0.2, "h": 0.05,
                                   "label": "a rather long label that needs several lines inside a narrow box"}]}
    svgs, _ = R.render_pages(d)
    assert "narrow" in "".join(svgs) and "several" in "".join(svgs)  # the whole label is drawn, wrapped over lines
    panel["staging"]["props"][0]["kind"] = "sign"
    errors, _ = V.validate(d)
    assert any("sign" in e for e in errors)  # retired: a sign is a box


def test_a_topic_comic_names_every_source_in_the_header_and_footer(doc):
    d = copy.deepcopy(doc)
    src = d["meta"].pop("source")
    d["meta"]["sources"] = [
        {"id": "one", **src, "authors": ["Craig, C.", "Killick, J."], "year": 2011, "licence": "CC BY 4.0"},
        {"id": "two", **src, "title": "Another reading", "authors": ["Beard, R."], "year": 2012, "licence": "All rights reserved"},
    ]
    for c in d["claims"]:
        c["source"]["ref"] = "one"
    svgs, _ = R.render_pages(d)
    assert "Drawn from 2 sources: Craig &amp; Killick (2011); Beard (2012)" in svgs[0].replace("&amp;amp;", "&amp;")
    assert "Another reading" in svgs[-1] and "Licence: All rights reserved." in svgs[-1]
    assert "Some of these sources are not under an open licence" in svgs[-1]


def test_the_new_faces_are_separate_from_the_five_original_ones_and_match_the_schema():
    import json
    assert not set(F.NEW) & set(F.LEGACY) and set(F.ALL) == set(F.LEGACY) | set(F.NEW)
    schema = json.loads((ROOT / "schema" / "storyboard.schema.json").read_text())
    enums = []

    def walk(o):
        if isinstance(o, dict):
            if "properties" in o and "face" in o["properties"] and "enum" in o["properties"]["face"]:
                enums.append(set(o["properties"]["face"]["enum"]))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(schema)
    assert enums and all(e == set(F.ALL) for e in enums)


def test_every_new_face_draws_with_and_without_glasses_on_a_stick_figure_and_a_diatom():
    pen = R.Pen("faces")
    for face in F.NEW:
        for glasses in (False, True):
            svg, head = R.figure(pen, 100, 200, 1.0, "stand", face, "right", None, {"glasses": glasses, "hair": "bob"})
            ET.fromstring(f"<g xmlns='http://www.w3.org/2000/svg'>{svg}</g>")
        svg, head = R.figure(pen, 100, 200, 1.0, "stand", face, "left", None, {"body": "diatom"})
        ET.fromstring(f"<g xmlns='http://www.w3.org/2000/svg'>{svg}</g>")


def test_every_new_face_has_an_animal_stand_in_among_the_five_original_faces():
    from animals import ANIMALS
    assert set(F.ANIMAL_FACE) == set(F.NEW) - {"surprised"} and set(F.ANIMAL_FACE.values()) <= set(F.ANIMAL_NATIVE)
    pen = R.Pen("animals2")
    for name in ANIMALS:
        for face in F.NEW:
            svg, head = R.figure(pen, 100, 200, 1.0, "stand", face, "right", None, {"body": name})
            ET.fromstring(f"<g xmlns='http://www.w3.org/2000/svg'>{svg}</g>")


def test_brows_stay_inside_the_head_and_the_original_faces_have_none():
    import math
    for face in F.NEW:
        out = F.draw_face(R.Pen(face), 100, 100, 1.0, face, 2.3)
        assert out
    for face in F.LEGACY:
        assert 'stroke="#ffffff"' not in "".join(R._face(R.Pen(face), 100, 100, 1.0, face, 2.3))  # the halo of a brow
    # an extreme brow is clamped to the head's outline (radius 15 s)
    checked = 0
    for style in (k for k, v in F.BROWS.items() if v):
        for seg in F._brows(R.Pen("b"), style, (99, 108.5), 97, 1.0, 2.3, False, 100, 100):
            for m in re.finditer(r'M([\d.]+) ([\d.]+)C.*? ([\d.]+) ([\d.]+)"', seg):
                x0, y0, x1, y1 = map(float, m.groups())
                for x, y in ((x0, y0), (x1, y1)):
                    checked += 1
                    assert math.hypot(x - 100, y - 100) <= 15.5, (style, x, y)
    assert checked > 20  # the pattern really found the brow ends


@pytest.mark.parametrize("hair", ["short", "shoulder", "beret", "boater", "flatcap"])
@pytest.mark.parametrize("tone", ["dark", "light", "grey"])
def test_the_new_hair_and_hats_draw_in_every_tone(hair, tone):
    svg, head = R.figure(R.Pen("hair"), 100, 200, 1.0, "stand", "smile", "right", None, {"hair": hair, "hair_tone": tone})
    ET.fromstring(f"<g xmlns='http://www.w3.org/2000/svg'>{svg}</g>")
    assert head[1] < 200 - 100  # the head point is above the head


def test_a_hat_takes_the_tone_as_its_colour_and_grey_uses_the_palettes_mid_grey():
    import draw
    black = R.figure(R.Pen(1), 100, 200, 1.0, "stand", "smile", "right", None, {"hair": "boater"})[0]
    white = R.figure(R.Pen(1), 100, 200, 1.0, "stand", "smile", "right", None, {"hair": "boater", "hair_tone": "light"})[0]
    grey = R.figure(R.Pen(1), 100, 200, 1.0, "stand", "smile", "right", None, {"hair": "flatcap", "hair_tone": "grey"})[0]
    assert black != white and f'fill="{draw.INK}"' in black and f'fill="{draw.MID}"' in grey and R.HAIR_GREY == draw.MID




def test_a_seated_figure_sits_lower_and_a_diatom_ignores_the_pose():
    stand = R.figure(R.Pen(1), 100, 300, 1.0, "stand", "smile", "right", None, {})
    sit = R.figure(R.Pen(1), 100, 300, 1.0, "sit", "smile", "right", "mug", {})
    assert sit[1][1] > stand[1][1] + 8  # its head is lower: the hips are at seat height, not standing height
    ET.fromstring(f"<g xmlns='http://www.w3.org/2000/svg'>{sit[0]}</g>")
    R.figure(R.Pen(1), 100, 300, 1.0, "sit", "smile", "right", None, {"body": "diatom"})
    R.figure(R.Pen(1), 100, 300, 1.0, "sit", "smile", "right", None, {"body": "krill"})


def test_head_scale_enlarges_the_head_and_the_default_is_1_2():
    default = R.figure(R.Pen(1), 100, 200, 1.0, "stand", "smile", "right", None, {"hair": "bob"})
    explicit = R.figure(R.Pen(1), 100, 200, 1.0, "stand", "smile", "right", None, {"hair": "bob", "head_scale": R.HEAD_SCALE})
    original = R.figure(R.Pen(1), 100, 200, 1.0, "stand", "smile", "right", None, {"hair": "bob", "head_scale": 1.0})
    big = R.figure(R.Pen(1), 100, 200, 1.0, "stand", "smile", "right", None, {"hair": "bob", "head_scale": 1.4})
    assert R.HEAD_SCALE == 1.2 and default == explicit
    assert big[1][1] < default[1][1] < original[1][1] - 2  # the head point is higher the bigger the head
    ET.fromstring(f"<g xmlns='http://www.w3.org/2000/svg'>{big[0]}</g>")




def _stage(st, w=420, h=260):
    return R.stage(R.Pen(1), 0, 0, w, h, st, {}, 18)


def test_no_shot_and_mid_draw_the_same_and_a_figures_own_scale_beats_the_preset():
    chars = [{"id": "a", "x": 0.4, "y": 0.9, "scale": 1.0, "face": "smile"}]
    assert _stage({"characters": chars}) == _stage({"shot": "mid", "characters": chars})
    assert _stage({"characters": chars}) == _stage({"shot": "close", "characters": chars})  # scale, x and y all given: nothing to fill in
    assert _stage({"characters": chars}) == _stage({"shot": "wide", "ground": False, "characters": chars})


def test_a_close_shot_fills_the_panel_with_the_head_and_a_wide_shot_makes_it_small():
    h = 260
    _, close = _stage({"shot": "close", "characters": [{"id": "a"}]}, h=h)
    _, wide = _stage({"shot": "wide", "characters": [{"id": "a"}]}, h=h)
    _, mid = _stage({"characters": [{"id": "a"}]}, h=h)
    assert 0 < close["a"][1] < 0.3 * h  # the top of the head is near the top of the scene, and inside it
    assert 0.35 * h < wide["a"][1] and mid["a"][1] < wide["a"][1]  # a small figure's head is lower than a mid one's
    assert abs(close["a"][0] - 210) < 1  # centred


def test_a_wide_shot_draws_a_ground_line_unless_told_not_to():
    chars = [{"id": "a"}]
    with_ground = _stage({"shot": "wide", "characters": chars})[0]
    without = _stage({"shot": "wide", "ground": False, "characters": chars})[0]
    assert len(with_ground) > len(without)


def test_two_figures_in_a_close_shot_sit_side_by_side():
    _, heads = _stage({"shot": "close", "characters": [{"id": "a"}, {"id": "b"}]})
    assert heads["a"][0] < 210 < heads["b"][0]


def test_the_schema_accepts_a_shot_and_refuses_one_it_does_not_know(doc):
    from validate_storyboard import validate
    d = copy.deepcopy(doc)
    d["beats"][0]["panels"][0].setdefault("staging", {})["shot"] = "close"
    assert validate(d)[0] == []
    d["beats"][0]["panels"][0]["staging"]["shot"] = "far"
    assert validate(d)[0] != []


def test_a_close_shot_with_three_figures_is_warned_about(doc):
    from validate_storyboard import validate
    d = copy.deepcopy(doc)
    d["beats"][0]["panels"][0].setdefault("staging", {}).update({"shot": "close", "characters": [{"id": "extra"}, {"id": "extra"}, {"id": "extra"}]})
    assert any("close-up shows one or two figures" in w for w in validate(d)[1])


def _prop(kind, **kw):
    import props as P
    return P.extra_prop(R.Pen(1), 0, 0, 400, 260, {"kind": kind, **kw}, 16)


def test_gallery_options_each_add_something_and_frames_changes_the_count():
    base = _prop("gallery")
    assert len(_prop("gallery", bench=True)) > len(base) and len(_prop("gallery", ramp=True)) > len(base) and len(_prop("gallery", easels=2)) > len(base)
    assert len(_prop("gallery", frames=5)) > len(_prop("gallery", frames=1))


def test_door_lock_and_open_change_the_drawing_and_a_cloud_fades_to_dashes():
    assert len(_prop("door", locked=True)) > len(_prop("door")) and _prop("door", open=True) != _prop("door")
    assert "stroke-dasharray" in _prop("cloud", faded=True) and "stroke-dasharray" not in _prop("cloud")


def test_scales_tilt_moves_the_beam_and_a_cycle_draws_an_arrowhead_per_stage():
    assert _prop("scales", tilt="left") != _prop("scales", tilt="right") != _prop("scales")
    items = [{"label": "a"}, {"label": "b"}, {"label": "c"}, {"label": "d"}]
    assert _prop("cycle", items=items).count("<path") >= 4 * 3  # an arc and two head strokes for each stage
    assert _prop("cycle", items=items[:3]).count("<circle") == 3  # a dot on the ring for each stage


def test_a_book_prints_its_title_and_a_skyline_marks_its_places():
    assert "Hello" in _prop("book", title="Hello") and "Hello" not in _prop("book")
    assert _prop("skyline", markers=3).count("<circle") == _prop("skyline").count("<circle") + 3


def test_a_staff_draws_one_head_per_pitch_and_a_time_signature():
    five = _prop("staff", pitches=[0, 2, 4, 6, 8])
    assert _prop("staff", pitches=[1, 3]) != five
    assert len(_prop("staff", pitches=[0, 2, 4, 6, 8])) > len(_prop("staff", pitches=[0, 2]))
    assert ">3<" in _prop("staff", meter="3/4") and ">4<" in _prop("staff", meter="3/4") and ">4<" in _prop("staff")


def test_brain_highlight_and_tracts_add_to_the_plain_brain_and_each_lobe_differs():
    base = _prop("brain")
    assert len(_prop("brain", tracts=True)) > len(base) and len(_prop("brain", highlight="frontal")) > len(base)
    assert len({_prop("brain", highlight=r) for r in ("frontal", "parietal", "temporal", "occipital")}) == 4


def test_livingroom_lamp_gears_and_funnel_labels_each_draw_something_more():
    assert len(_prop("livingroom", lamp=True)) > len(_prop("livingroom"))
    two = [{"label": "speech"}, {"label": "song"}]
    assert "speech" in _prop("gears", items=two) and "speech" not in _prop("gears")
    assert "song" in _prop("gears", items=two) and "song" not in _prop("gears")
    assert "kept" in _prop("funnel", items=[{"label": "all"}, {"label": "kept"}]) and "kept" not in _prop("funnel")


def test_stage_options_each_draw_something_more_and_a_prop_can_be_empty_blank_or_missing():
    assert len(_prop("stage", spotlight=True)) > len(_prop("stage")) and len(_prop("stage", audience=True)) > len(_prop("stage")) and len(_prop("stage", screen=True)) > len(_prop("stage"))
    assert len(_prop("gallery", frames=3, empty=1)) != len(_prop("gallery", frames=3)) and "?" in _prop("gallery", frames=3, empty=1) and "?" not in _prop("gallery", frames=3)
    assert "stroke-dasharray" in _prop("book", blank=True) and "stroke-dasharray" not in _prop("book", title="T") and "?" in _prop("book", blank=True)
    assert "stroke-dasharray" in _prop("bookshelf", gap=True) and "?" in _prop("bookshelf", gap=True) and "?" not in _prop("bookshelf") and len(_prop("bookshelf", gap=True, lit=True)) > len(_prop("bookshelf", gap=True))
    assert len(_prop("brain", signal=True)) > len(_prop("brain"))


def test_idea_props_take_their_labels_and_options():
    two = [{"label": "input"}, {"label": "output"}]
    assert "input" in _prop("blackbox", items=two) and "input" not in _prop("blackbox") and "?" in _prop("blackbox")
    assert "stroke-dasharray" in _prop("blackbox", dashed=True) and "stroke-dasharray" not in _prop("blackbox")
    assert "art" in _prop("bridge", items=[{"label": "art"}, {"label": "health"}]) and _prop("bridge", broken=True) != _prop("bridge")
    assert len(_prop("eye", lens=True)) > len(_prop("eye")) and "what next" in _prop("eye", thought="what next") and "what next" not in _prop("eye", thought=True)
    assert len(_prop("hospitalroom", drip=True)) > len(_prop("hospitalroom"))
    assert len(_prop("spinalcord", laminae=True)) > len(_prop("spinalcord")) and _prop("spinalcord", hemisection=True) != _prop("spinalcord")


def test_a_circle_of_chairs_has_one_chair_per_seat_and_its_centre():
    count = lambda **kw: _prop("circle", **kw).count("<path")  # noqa: E731
    assert count(chairs=3) < count(chairs=6) < count(chairs=8)
    assert all(count(chairs=5, centre=c) != count(chairs=5) for c in ("fire", "easel", "person"))


def test_a_split_screen_draws_both_halves_and_speech_can_point_at_a_figure_in_either(doc):
    from validate_storyboard import validate
    d = copy.deepcopy(doc)
    panel = d["beats"][0]["panels"][0]
    ids = [c["id"] for c in d["cast"]][:2]
    panel["staging"] = {"split": [{"characters": [{"id": ids[0], "x": 0.5, "face": "smile"}]}, {"characters": [{"id": ids[1], "x": 0.5, "face": "worry"}]}], "split_labels": ["before", "after"]}
    panel["speech"] = [{"speaker": ids[1], "kind": "say", "text": "Then it came apart."}]
    assert validate(d)[0] == []  # the schema accepts a split, and a speaker staged in a half counts as staged
    text = "".join(R.render_pages(d)[0])
    assert "before" in text and "after" in text and "Then it came apart." in text
    heads = R.stage(R.Pen(1), 0, 0, 400, 300, panel["staging"], {c["id"]: c for c in d["cast"]}, 16)[1]
    assert ids[0] in heads and ids[1] in heads and heads[ids[0]][0] < heads[ids[1]][0]  # left half first, then right


def test_the_catalogue_and_the_row_planner_see_props_and_characters_inside_a_split():
    import catalogue
    st = {"split": [{"props": [{"kind": "cloud"}]}, {"props": [{"kind": "bridge"}], "characters": [{"id": "extra", "body": "puppet"}]}]}
    assert [p["kind"] for p in catalogue.walk_props(st)] == ["cloud", "bridge"]
    row = [({"staging": st, "id": "x"}, 12)]
    assert R._row_limits(row, [{"scene_nat": 100, "shrink_ok": 1.0}], 100)["rich"] > R._row_limits([({"staging": {}, "id": "x"}, 12)], [{"scene_nat": 100, "shrink_ok": 1.0}], 100)["rich"]


@pytest.mark.parametrize("direction", ["side", "stack", "slope"])
def test_a_split_can_be_cut_three_ways_and_each_half_still_draws_its_figure_and_label(doc, direction):
    from validate_storyboard import validate
    d = copy.deepcopy(doc)
    panel = d["beats"][0]["panels"][0]
    ids = [c["id"] for c in d["cast"]][:2]
    panel["staging"] = {"split": [{"characters": [{"id": ids[0], "x": 0.25}]}, {"characters": [{"id": ids[1], "x": 0.75}]}], "split_labels": ["first", "second"], "split_direction": direction}
    panel["speech"] = [{"speaker": ids[1], "kind": "say", "text": "Over here."}]
    assert validate(d)[0] == []
    text = "".join(R.render_pages(d)[0])
    assert "first" in text and "second" in text and "Over here." in text
    assert ('id="split-' in text) == (direction == "slope")  # only a slanted divider needs clipping
    heads = R.stage(R.Pen(1), 0, 0, 400, 300, panel["staging"], {c["id"]: c for c in d["cast"]}, 16)[1]
    assert set(ids) <= set(heads)
    off = R.staged_offsets(panel["staging"], {c["id"]: c for c in d["cast"]}, 400, 300)
    assert set(ids) <= set(off)
    if direction == "stack":
        assert heads[ids[0]][1] < heads[ids[1]][1]  # the first half is above the second
    else:
        assert heads[ids[0]][0] < heads[ids[1]][0]  # the first half is left of the second


def test_an_unknown_split_direction_is_refused_by_the_schema(doc):
    from validate_storyboard import validate
    d = copy.deepcopy(doc)
    d["beats"][0]["panels"][0]["staging"] = {"split": [{}, {}], "split_direction": "diagonal"}
    assert validate(d)[0]
