import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import topic_from_cards as tc  # noqa: E402


def card(i, kind="result", page=3, text="A finding.", quote="q"):
    return {"id": i, "text": text, "kind": kind, "source": {"page": page, "quote": quote}}


INDEX = {
    "k:C1": card("C1", text="The program has run since 2010.", quote="since 2010"),
    "k:C2": card("C2", "future_research", 16, "More research is needed on curating art."),
    "c:C1": card("C1", text="Twenty-four participants completed the study.", quote="24 participants"),
    "c:C2": card("C2", "caveat", 8, "The sample was small."),
}
LABELS = {"k": "Kenning 2016", "c": "Camic 2014"}


def item(text, *cites):
    return {"text": text, "cites": list(cites)}


def test_a_statement_that_cites_real_cards_and_uses_their_numbers_is_kept():
    kept, rej = tc.check({"synthesis": [item("It has run since 2010 and 24 completed one study.", "k:C1", "c:C1")]}, INDEX)
    assert len(kept["synthesis"]) == 1 and not rej


def test_a_statement_with_no_card_or_a_made_up_card_is_dropped():
    _, rej = tc.check({"synthesis": [item("Unsupported.", ), item("Fake.", "k:C99")]}, INDEX)
    assert "cites no card" in rej[0]["why"] and "does not exist: k:C99" in rej[1]["why"]


def test_a_number_the_cited_cards_do_not_contain_is_dropped():
    _, rej = tc.check({"synthesis": [item("About 900 people took part.", "k:C1")]}, INDEX)
    assert "900" in rej[0]["why"]


def test_a_tension_needs_two_papers_and_an_open_question_needs_a_call_for_research_or_a_limitation():
    kept, rej = tc.check({"tensions": [item("They differ.", "k:C1", "c:C1"), item("One paper only.", "k:C1")],
                          "open_questions": [item("What next?", "k:C2"), item("Why?", "k:C1")]}, INDEX)
    assert len(kept["tensions"]) == 1 and len(kept["open_questions"]) == 1
    assert {r["section"] for r in rej} == {"tensions", "open_questions"}


def test_citations_are_rendered_as_paper_and_pages():
    assert tc.cite_text(["k:C1", "c:C2", "c:C1"], INDEX, LABELS) == "(Kenning 2016, p.3; Camic 2014, p.3,8)"


def test_the_page_lists_a_paper_none_of_whose_cards_were_cited():
    kept = {"synthesis": [item("Since 2010.", "k:C1")], "tensions": [], "open_questions": []}
    page = tc.render("Gallery programs", kept, [], INDEX, LABELS, ["k", "c"], model="m")
    assert "Camic 2014 (none of its cards were cited above)" in page and "Not used in the statements above: Camic 2014" in page
    assert "generated_by: cards" in page and "reviewed: false" in page


def test_a_reply_that_is_not_json_gives_an_empty_page_not_an_error():
    assert tc.parse("not json") == {}
    kept, rej = tc.check({}, INDEX)
    assert kept == {"synthesis": [], "tensions": [], "open_questions": []} and not rej


def test_a_ref_prefix_the_model_adds_is_dropped_when_the_card_exists():
    idx = {"camic:C5": {"text": "Eight people took part.", "kind": "result", "source": {"page": 3, "quote": "eight people"}},
           "kenning:C1": {"text": "Tours ran weekly.", "kind": "method", "source": {"page": 2, "quote": "weekly"}}}
    reply = {"synthesis": [{"text": "Tours ran weekly (Kenning).", "cites": ["ref:kenning:C1"]}], "tensions": [], "open_questions": []}
    kept, rejected = tc.check(reply, idx)
    assert not rejected and kept["synthesis"][0]["cites"] == ["kenning:C1"]
    kept, rejected = tc.check({"synthesis": [{"text": "x", "cites": ["ref:nothing:C9"]}]}, idx)
    assert rejected and "does not exist" in rejected[0]["why"]


def test_a_year_in_a_papers_own_label_is_not_an_unsupported_number_but_another_year_is():
    idx = {"roden:C5": {"text": "Children had weekly lessons.", "kind": "method", "source": {"page": 3, "quote": "weekly lessons"}}}
    labels = {"roden": "Roden 2014"}
    ok = {"synthesis": [{"text": "Roden 2014 gave weekly lessons.", "cites": ["roden:C5"]}]}
    bad = {"synthesis": [{"text": "Roden (2013) gave weekly lessons.", "cites": ["roden:C5"]}]}
    assert not tc.check(ok, idx, labels)[1]
    kept, rejected = tc.check(bad, idx, labels)
    assert rejected and "2013" in rejected[0]["why"]
    assert tc.check(ok, idx)[1]  # with no labels given, the year is still unsupported
