import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_quotes import check, contains, load_pages, main, tokens  # noqa: E402

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
