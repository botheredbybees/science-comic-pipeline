import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import story_arcs as sa  # noqa: E402

PAGE = """---
title: Gallery programs
---

## Gallery programs

## Synthesis

Programs ran for 8 weeks. (Kenning 2016, p.3)

Carers also took part. (Camic 2014, p.2,5; Kenning 2016, p.4)

## Where the papers differ

Kenning 2016 found gains; Camic 2014 found none. (Kenning 2016, p.3; Camic 2014, p.2)

## Open questions

- Who benefits most? (Camic 2014, p.8)

## Papers

- Kenning 2016
- Camic 2014 (none of its cards were cited above)
"""
TITLE, LABELS, ST = sa.parse_topic(PAGE)


def beat(text, role, *cites):
    return {"role": role, "text": text, "cites": list(cites)}


def arc(*beats):
    return {"name": "A", "shape": "two sides", "logline": "x", "beats": list(beats)}


def good(n=3):
    return [beat("Programs ran for 8 weeks.", "setup", "S1"), beat("Carers took part.", "finding", "S2"), beat("Who benefits most is open.", "open", "S4")][:n]


def test_the_topic_page_is_read_into_numbered_statements_by_section():
    assert TITLE == "Gallery programs" and LABELS == ["Kenning 2016", "Camic 2014"]
    assert [(s["id"], s["section"]) for s in ST] == [("S1", "finding"), ("S2", "finding"), ("S3", "tension"), ("S4", "open")]
    assert ST[1]["cite"] == "(Camic 2014, p.2,5; Kenning 2016, p.4)" and ST[1]["text"] == "Carers also took part."


def test_beats_that_cite_real_statements_and_use_their_numbers_are_kept():
    arcs, rej = sa.check({"arcs": [arc(*good())]}, ST, LABELS)
    assert len(arcs) == 1 and len(arcs[0]["beats"]) == 3 and not rej


def test_a_beat_with_no_statement_a_made_up_one_or_a_number_not_in_them_is_dropped():
    bad = [beat("Unsupported.", "finding"), beat("Fake.", "finding", "S9"), beat("It ran for 12 weeks.", "finding", "S1")]
    arcs, rej = sa.check({"arcs": [arc(*(good() + bad))]}, ST, LABELS)
    assert len(arcs[0]["beats"]) == 3
    assert "cites no statement" in rej[0]["why"] and "does not exist: S9" in rej[1]["why"] and "12" in rej[2]["why"]


def test_a_tension_or_open_beat_must_cite_a_statement_from_that_section():
    bad = [beat("They differ.", "tension", "S1"), beat("Unknown.", "open", "S1")]
    arcs, rej = sa.check({"arcs": [arc(*(good() + bad))]}, ST, LABELS)
    assert len(arcs[0]["beats"]) == 3 and "tension beat" in rej[0]["why"] and "open beat" in rej[1]["why"]


def test_an_arc_with_fewer_than_three_surviving_beats_is_dropped_and_reported():
    arcs, rej = sa.check({"arcs": [arc(*good(2))]}, ST, LABELS)
    assert arcs == [] and "only 2 beat(s)" in rej[-1]["why"]


def test_a_year_in_a_paper_label_is_not_an_unsupported_number():
    arcs, rej = sa.check({"arcs": [arc(*good(2), beat("Kenning 2016 found gains.", "tension", "S3"))]}, ST, LABELS)
    assert len(arcs) == 1 and not rej


def test_the_page_shows_each_beat_with_its_statements_papers_and_pages_and_what_no_arc_used():
    arcs, rej = sa.check({"arcs": [arc(*good())]}, ST, LABELS)
    page = sa.render(TITLE, arcs, rej, ST, "p.md", "m")
    assert "experiment: true" in page and "reviewed: false" in page
    assert "1. **setup**: Programs ran for 8 weeks. (S1; Kenning 2016, p.3)" in page
    assert "Not used in any arc: S3" in page


def test_a_reply_that_is_not_json_gives_an_empty_page_not_an_error():
    assert sa.parse("nope") == {}
    arcs, rej = sa.check({}, ST, LABELS)
    assert arcs == [] and "No arc survived" in sa.render(TITLE, arcs, rej, ST, "p.md")
