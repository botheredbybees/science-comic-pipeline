import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from cards_to_source_page import main, meta_from_page, render  # noqa: E402


def card(n, kind="result", page=3, verdict=None, text=None):
    c = {"id": f"C{n}", "text": text or f"claim {n}", "kind": kind, "source": {"locator": f"page {page}", "page": page, "quote": f"quote {n}", "ref": "p"},
         "status": "unverified"}
    if verdict:
        c["model_check"] = {"verdict": verdict, "why": "says more"}
    return c


def test_sections_follow_the_kind_and_every_line_has_a_page_and_an_id():
    page = render([card(1, "background", 1), card(2, "method", 2), card(3, "result", 5), card(4, "caveat", 7), card(5, "future_research", 8)], {"title": "T"})
    for heading in ("## Background", "## Methods", "## Results", "## Caveats and limitations", "## Calls for further research"):
        assert heading in page
    assert "- claim 3 (p.5) `C3`" in page


def test_the_evidence_section_lists_every_quote_with_its_page():
    page = render([card(1, page=4), card(2, page=2)], {"title": "T"})
    assert page.index('`C2` p.2: "quote 2"') < page.index('`C1` p.4: "quote 1"')  # in page order


def test_flagged_cards_are_kept_apart_from_the_findings():
    page = render([card(1, verdict="supported"), card(2, verdict="overstated")], {"title": "T"})
    body = page.split("## Needs review")[0]
    assert "claim 1" in body and "claim 2" not in body
    assert "claim 2" in page.split("## Needs review")[1].split("## Evidence")[0] and "**overstated**" in page


def test_the_frontmatter_says_the_page_is_unreviewed_and_counts_cards_and_pages():
    page = render([card(1, page=1), card(2, page=3, verdict="unclear")], {"title": "T", "slug": "s"}, n_pages=10)
    fm = yaml.safe_load(page.split("---")[1])
    assert fm["generated_by"] == "cards" and fm["reviewed"] is False and fm["cards"] == 2 and fm["cards_flagged"] == 1
    assert fm["pages_with_cards"] == "2 of 10" and fm["slug"] == "s"


def test_graphics_are_added_as_a_section():
    g = [{"title": "Timeline", "shows": "the start in 2010", "claim_ids": ["C1"], "element": {"kind": "axis"}},
         {"title": "Gallery wall", "shows": "paintings", "claim_ids": ["C2"], "element": {"kind": "new"}, "new_asset": "gallery wall"}]
    page = render([card(1), card(2)], {"title": "T"}, graphics=g)
    assert "## Suggested graphic elements" in page and "Use `axis`." in page and "a new asset: gallery wall" in page


def test_meta_is_copied_from_an_existing_page_even_with_a_byte_order_mark(tmp_path):
    p = tmp_path / "old.md"
    p.write_text('﻿---\ntype: source\ntitle: "Old"\napa7: "A (2020)."\ndoi: null\nslug: old\ntags: ["a", "b"]\n---\n\nbody\n', encoding="utf-8")
    m = meta_from_page(p)
    assert m == {"title": "Old", "apa7": "A (2020).", "slug": "old", "tags": ["a", "b"]}


def test_cli_counts_pages_from_the_cards_folder(tmp_path):
    folder = tmp_path / "paper"
    (folder / "pages").mkdir(parents=True)
    for i in (1, 2, 3):
        (folder / "pages" / f"p00{i}.txt").write_text("x")
    (folder / "cards.yaml").write_text(yaml.safe_dump({"claims": [card(1, page=1)]}))
    out = tmp_path / "out" / "p.md"
    assert main([str(folder / "cards.yaml"), "-o", str(out), "--title", "T"]) == 0
    assert "pages_with_cards: 1 of 3" in out.read_text()


def test_a_key_selection_leads_the_page_and_leaves_omitted_cards_off_it_entirely():
    cards = [card(1, "result", 2, text="main finding"), card(2, "background", 3, text="minor detail"),
             card(3, "background", 4, text="Karl was diagnosed with dementia at an early age")]
    page = render(cards, {"title": "T"}, key={"key": ["C1"], "omit": ["C3"]})
    assert page.index("## Key points") < page.index("main finding") < page.index("## More detail") < page.index("minor detail")
    assert "Karl" not in page and "`C3`" not in page  # not in the body, and not in the evidence either
    assert yaml.safe_load(page.split("---")[1])["cards_left_off"] == 1
