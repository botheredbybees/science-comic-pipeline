import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "renderers" / "xkcd"))
sys.path.insert(0, str(ROOT / "scripts"))
import asset_gallery  # noqa: E402
import render as R  # noqa: E402
from animals import ANIMALS  # noqa: E402
from props import EXTRA  # noqa: E402
from validate_storyboard import validate  # noqa: E402


def test_the_gallery_is_a_valid_storyboard_and_renders():
    doc = asset_gallery.build()
    errors, _ = validate(doc)
    assert errors == []
    svgs, _ = R.render_pages(doc)
    assert svgs and "not under an open licence" not in svgs[-1] and "Read the original paper" not in svgs[-1]


def _schema_enum(path):
    node = json.loads((ROOT / "schema" / "storyboard.schema.json").read_text())
    for key in path:
        node = node[key]
    return set(node["enum"])


def _walk_props(staging):
    for pr in (staging or {}).get("props", []):
        yield pr
        yield from _walk_props(pr.get("staging"))


def test_the_gallery_shows_every_body_every_prop_and_every_held_object():
    """The lists come from the schema, so an asset added to the schema but not to the gallery fails here."""
    doc = asset_gallery.build()
    panels = [p for b in doc["beats"] for p in b["panels"]]
    chars = [c for p in panels for c in (p.get("staging") or {}).get("characters", [])]
    bodies = {c.get("body") for c in chars}
    held = {c.get("holding") for c in chars}
    kinds = {pr["kind"] for p in panels for pr in _walk_props(p.get("staging"))}
    defs = ("$defs", "staging", "properties")
    all_kinds = _schema_enum(defs + ("props", "items", "properties", "kind"))
    all_held = _schema_enum(defs + ("characters", "items", "properties", "holding"))
    assert not (set(ANIMALS) | {"diatom"}) - bodies, (set(ANIMALS) | {"diatom"}) - bodies
    assert not all_kinds - kinds, all_kinds - kinds
    assert not all_held - held, all_held - held


def _enums_containing(value):
    found = []

    def walk(node):
        if isinstance(node, dict):
            if value in node.get("enum", []):
                found.append(set(node["enum"]))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(json.loads((ROOT / "schema" / "storyboard.schema.json").read_text()))
    return found


def test_the_gallery_shows_every_hair_style_tone_and_clothing_option():
    doc = asset_gallery.build()
    looks = [c.get("appearance", {}) for c in doc["cast"]]
    for enum_value, field in (("beanie", "hair"), ("strands", "hair_tone")):
        enums = _enums_containing(enum_value)
        assert enums, enum_value
        shown = {a.get(field) for a in looks}
        for enum in enums:
            assert not enum - shown - {None, "dark"}, (field, enum - shown)  # "dark" is the default tone
    assert any(a.get("glasses") for a in looks) and any(a.get("coat") for a in looks)
    outfits = _enums_containing("floatcoat")
    assert outfits
    for enum in outfits:
        assert not enum - {a.get("outfit") for a in looks}, enum


def test_the_whole_gallery_uses_only_black_white_and_grey():
    """Every fill and stroke of every body, prop, held object and look is one of the four palette tones."""
    import re
    import draw
    palette = {draw.INK, draw.PAPER, draw.SOFT, draw.MID, "none"}
    svgs, _ = R.render_pages(asset_gallery.build())
    used = set()
    for svg in svgs:
        used |= set(re.findall(r'(?:fill|stroke)="(#[0-9a-fA-F]{3,6}|[a-zA-Z]+)"', svg))
    assert used <= palette, used - palette
