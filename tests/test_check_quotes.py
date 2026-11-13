import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_quotes import check, contains, contains_quote, dashes, load_pages, main, tokens  # noqa: E402

PAGES = {
    1: "The flash must be short, 100-200 µs,\nlonger than that and downstream carriers fill too.",
    2: "Averaging cuts noise roughly as 1/√N. The ﬁrst trans-\nient is noisy.",
}


def claim(cid, text, quote, page, status="verified"):
    src = {"locator": "x"}
    if quote is not None:
        src["quote"] = quote
    if page is not None:
        src["page"] = page
    return {"id": cid, "text": text, "kind": "result", "source": src, "status": status}


def run(*claims):
    return check({"claims": list(claims)}, PAGES)


def test_tokens_ignore_case_punctuation_ligatures_and_hyphenated_line_breaks():
    assert tokens("The ﬁrst trans-\nient") == ["the", "first", "transient"]


def test_quote_found_across_a_line_break():
    errors, warnings = run(claim("C1", "The flash is short.", "short, 100-200 µs, longer than that", 1))
    assert errors == []


def test_quote_must_be_on_the_named_page():
    errors, _ = run(claim("C1", "x", "noise roughly as 1/√N", 1))
    assert any("not found on page 1" in e and "[2]" in e for e in errors)


def test_a_verified_claim_needs_a_quote_and_a_page():
    errors, _ = run(claim("C1", "x", None, None), claim("C2", "x", "short", None))
    assert len(errors) == 2


def test_an_unverified_claim_without_a_quote_only_warns():
    errors, warnings = run(claim("C1", "x", None, None, status="unverified"))
    assert errors == [] and warnings


def test_number_in_claim_but_not_in_quote_is_a_warning():
    _, warnings = run(claim("C1", "The flash lasts 150 µs.", "short, 100-200 µs", 1))
    assert any("150" in w for w in warnings)


def test_numbers_that_are_in_the_quote_do_not_warn():
    _, warnings = run(claim("C1", "The flash lasts 100 to 200 µs.", "short, 100-200 µs", 1))
    assert warnings == []


def test_page_missing_from_source_is_an_error():
    errors, _ = run(claim("C1", "x", "short", 9))
    assert any("page 9 is not in the source" in e for e in errors)


def test_contains_needs_a_contiguous_match():
    assert contains(["a", "b", "c"], ["b", "c"]) and not contains(["a", "b", "c"], ["a", "c"])


def test_cli_with_a_pages_dir(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "p001.txt").write_text(PAGES[1])
    sb = tmp_path / "s.yaml"
    sb.write_text("claims:\n  - {id: C1, text: 'x', kind: result, status: verified, source: {locator: p, quote: 'downstream carriers fill', page: 1}}\n")
    assert main([str(sb), "--pages-dir", str(pages)]) == 0
    assert load_pages(pages_dir=pages) == {1: PAGES[1]}


def test_locator_is_checked_against_the_page_map(tmp_path):
    import check_quotes as cq
    pages = {1: "Alpha beta gamma."}
    doc = {"claims": [{"id": "C1", "text": "Alpha", "status": "verified",
                       "source": {"page": 1, "quote": "Alpha beta", "locator": "Methods, Field sampling, paragraph 2"}}]}
    ok = {1: ("Methods / Field sampling", 2)}
    bad = {1: ("Methods / Field sampling", 3)}
    assert cq.check(doc, pages, ok)[1] == []
    assert any("locator" in w for w in cq.check(doc, pages, bad)[1])


def test_locator_headings_with_commas_and_numbers_and_rrna_labels_are_fine():
    import check_quotes as cq
    pages = {1: "rRNA gene copies vary"}
    doc = {"claims": [{"id": "C1", "text": "The 18S rRNA gene copies vary.", "status": "verified",
                       "source": {"page": 1, "quote": "rRNA gene copies vary", "locator": "3. Results, 3.2. Fv/Fm, light and stress, paragraph 1"}}]}
    locs = {1: ("3. Results / 3.2. Fv/Fm, light and stress", 1)}
    assert cq.check(doc, pages, locs) == ([], [])


def test_soft_hyphen_at_a_line_end_joins_the_word():
    assert tokens("bio\u00ad\nmonitoring is useful") == ["biomonitoring", "is", "useful"]
    assert contains_quote("bio\u00ad\nmonitoring is useful", "biomonitoring is useful")


def test_a_real_hyphen_at_a_line_end_matches_either_reading():
    page = "a long-\nterm record and ap-\nproximately ten"
    assert contains_quote(page, "a long-term record")
    assert contains_quote(page, "approximately ten")


def test_fragments_must_all_appear_in_order():
    page = "alpha beta gamma\n\nunrelated words here\n\ndelta epsilon zeta"
    assert contains_quote(page, "alpha beta ... delta epsilon")
    assert contains_quote(page, "alpha beta \u2026 epsilon zeta")
    assert not contains_quote(page, "delta epsilon ... alpha beta")
    assert not contains_quote(page, "alpha beta ... theta")


def test_hint_when_only_the_first_word_is_wrong():
    pages = {1: "the previous word-\n\nglued continues with the claim text here"}
    errors, _ = check({"claims": [claim("C1", "x", "glued continues with the claim text here", 1)]}, pages)
    assert errors == []  # joined reading finds it
    pages = {1: "previous continues with the claim text here"}
    errors, _ = check({"claims": [claim("C1", "x", "wrongword continues with the claim text here", 1)]}, pages)
    assert errors and "one word later" in errors[0]


def test_warns_when_a_quote_contains_a_publisher_footer():
    pages = {1: "Downloaded from https://example.org by someone on a date"}
    _, warnings = check({"claims": [claim("C1", "x", "Downloaded from https://example.org by someone", 1)]}, pages)
    assert any("publisher footer" in w for w in warnings)


def test_dashes_are_normalised_for_locators():
    assert dashes("MZG\u2010ICE and a\u2013b") == "MZG-ICE and a-b"
