import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from intake_check import assess  # noqa: E402

PROSE = "The first wave arose in response to the Industrial Revolution and changed how cities handled water. " * 40


def test_a_normal_article_has_no_flags_and_a_licence_hint():
    r = assess("Abstract. " + PROSE * 6 + " This is an open access article under the CC BY 4.0 licence.", 8)
    assert r["flags"] == [] and "CC BY" in r["licence_hint"]


def test_a_scanned_file_is_flagged():
    assert "scanned" in assess("page 1 page 2", 10)["flags"]


def test_a_one_page_abstract_is_flagged():
    r = assess("Background. People with dementia. " * 30 + " (c) 2020 the Alzheimer's Association", 1)
    assert "abstract-only" in r["flags"] and "Alzheimer" in r["licence_hint"]


def test_a_bibliography_is_flagged_as_a_reference_list():
    refs = "Cormack, E. (2012). Contemporary art in healing environments. Craik, J. (2007). Re-Visioning Arts. Smith, A. B., & Jones, C. (2010). Title. " * 15
    assert "reference-list" in assess(refs, 3)["flags"]


def test_a_slice_from_the_middle_of_a_chapter_is_a_fragment():
    text = "somewhere in the middle of a discussion of results and methods " * 100 + " Printed page 2 of 15"
    assert "fragment" not in assess(text, 15)["flags"]  # page 2 of 15 is not page 1
    text1 = "mid text without a title or any heading at all just prose about sampling " * 100 + " Printed page 1 of 23"
    assert "fragment" in assess(text1, 23)["flags"]
