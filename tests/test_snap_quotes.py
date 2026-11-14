import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_quotes import contains_quote  # noqa: E402
from snap_quotes import snap, snap_claim  # noqa: E402

PAGE = ("The first wave, roughly 1830 to 1900, arose directly in response to the Industrial Revolution ( ). The imperative of the\n"
        "first wave was to make order out of disorder: human faeces had to be removed from the water supply and factories had to be made safe.")


def test_a_quote_that_dropped_a_citation_snaps_to_the_exact_page_text():
    exact, ratio = snap(PAGE, "The first wave, roughly 1830 to 1900, arose directly in response to the Industrial Revolution")
    assert exact and exact.endswith("Industrial Revolution") and ratio == 1.0
    assert contains_quote(PAGE, exact)


def test_a_tidied_quote_snaps_and_then_passes_the_checker():
    tidied = "Human faeces had to be removed from the water supply, and factories made safe"
    assert not contains_quote(PAGE, tidied)
    exact, ratio = snap(PAGE, tidied)
    assert exact and contains_quote(PAGE, exact) and ratio >= 0.75


def test_an_invented_quote_is_rejected_not_repaired():
    exact, ratio = snap(PAGE, "The second wave applied scientific rationalism together with technological change")
    assert exact is None and ratio < 0.75


def test_a_quote_credited_to_the_wrong_page_is_found_on_the_right_one():
    pages = {1: "Nothing relevant here at all, just filler words and numbers.", 2: PAGE}
    page, exact, ratio = snap_claim(pages, 1, "make order out of disorder: human faeces had to be removed from the water supply")
    assert page == 2 and exact and contains_quote(pages[2], exact)


def test_a_very_short_quote_is_refused():
    assert snap(PAGE, "first wave")[0] is None
