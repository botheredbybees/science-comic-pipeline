import copy
import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "renderers" / "xkcd"))
sys.path.insert(0, str(ROOT / "scripts"))
import render as R  # noqa: E402
from build_storyboard import build, main as build_main  # noqa: E402
from validate_storyboard import load_schema, validate  # noqa: E402
import jsonschema  # noqa: E402

EXAMPLE = ROOT / "examples" / "akam-2026-cartooning" / "storyboard.yaml"
EDNA = ROOT / "examples" / "southern-ocean-edna-agreement"
MORE = {"text": "The full comic", "url": "https://example.org/a/b/c/full.pdf"}


@pytest.fixture
def doc():
    return yaml.safe_load(EXAMPLE.read_text())


def link_text(svgs):
    return " ".join(re.findall(r">([^<>]+)<", "".join(svgs)))


def test_meta_more_needs_a_text_and_an_address(doc):
    schema = load_schema()
    doc["meta"]["more"] = dict(MORE)
    jsonschema.validate(doc, schema)
    for bad in ({"text": "x"}, {"url": MORE["url"]}, {**MORE, "url": "ftp://x"}):
        doc["meta"]["more"] = bad
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(doc, schema)


def test_the_footer_links_to_the_longer_comic(doc):
    doc["meta"]["more"] = dict(MORE)
    svgs, _ = R.render_pages(doc)
    last = svgs[-1]
    assert f'<a href="{MORE["url"]}"' in last and "The full comic: https://example.org/a/b/c/full.pdf" in link_text([last])


def test_a_private_comic_prints_no_link_to_a_longer_one(doc):
    doc["meta"]["more"] = dict(MORE)
    doc["meta"]["private"] = True
    svgs, _ = R.render_pages(doc)
    assert MORE["url"] not in "".join(svgs)


def test_a_long_address_is_broken_so_it_stays_on_the_page(doc):
    doc["meta"]["more"] = {"text": "The full comic", "url": "https://github.com/" + "/".join(["a-long-folder-name"] * 8) + "/full.pdf"}
    svgs, _ = R.render_pages(doc)
    per = int((R.PAGE_W - 2 * R.MARGIN) / (15 * R.CHAR_W))
    lines = [t for t in re.findall(r">([^<>]+)<", svgs[-1]) if "a-long-folder-name" in t or t.endswith("full.pdf")]
    assert len(lines) >= 2 and all(len(t) <= per for t in lines)


def test_a_second_ledger_can_serve_a_short_version(tmp_path):
    (tmp_path / "beats").mkdir()
    (tmp_path / "head.yaml").write_text(yaml.safe_dump({"version": 2, "meta": {"title": "T"}, "cast": []}))
    (tmp_path / "beats" / "B1.yaml").write_text(yaml.safe_dump(
        [{"id": "B1", "act": "problem", "panels": [{"id": "B1.1", "scene": "s", "claim_ids": ["C2"]}]}]))
    full = tmp_path / "full"
    full.mkdir()
    (full / "claims.yaml").write_text(yaml.safe_dump({"claims": [
        {"id": "C2", "text": "t", "kind": "background", "status": "verified", "source": {"locator": "x"}}]}))
    with pytest.raises(ValueError, match="not in any ledger"):
        build(tmp_path)
    out, _, _, _ = build(tmp_path, [full / "claims.yaml"])
    assert [c["id"] for c in out["claims"]] == ["C2"]
    assert build_main([str(tmp_path), "--claims", str(full / "claims.yaml")]) == 0


def test_the_edna_overview_is_one_page_that_validates_and_links_to_the_full_comic():
    out = EDNA / "overview" / "storyboard.yaml"
    d = yaml.safe_load(out.read_text())
    assert validate(d) == ([], [])
    svgs, _ = R.render_pages(d)
    assert len(svgs) == 1
    assert d["meta"]["more"]["url"].endswith("southern-ocean-edna-agreement.pdf")
    assert {c["id"] for c in d["claims"]} <= {c["id"] for c in yaml.safe_load((EDNA / "storyboard.yaml").read_text())["claims"]}
