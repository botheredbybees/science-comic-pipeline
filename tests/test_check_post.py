import copy
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import check_post as CP  # noqa: E402

CLAIMS = [
    {"id": "C1", "text": "Approximately 40% of reads were assigned to Metazoa in both sample types.", "kind": "result", "status": "verified",
     "source": {"ref": "x", "locator": "Results", "page": 3, "quote": "Approximately 40% of reads were assigned to Metazoa in both sample types"}},
    {"id": "C2", "text": "Ten laboratories analysed shared samples; most groups clustered them by ocean region.", "kind": "result", "status": "verified",
     "source": {"ref": "x", "locator": "Results", "page": 4, "quote": "Ten laboratories analysed shared samples; most groups clustered them by ocean region"}},
    {"id": "C3", "text": "A claim nobody checked.", "kind": "result", "status": "unverified"},
]
PANELS = [{"id": "B1.1", "scene": "s", "speech": [], "claim_ids": ["C1"]},
          {"id": "B1.2", "scene": "s", "speech": [], "claim_ids": ["C1"],
           "humour": {"note": "a joke", "keeps_claims_intact": False}}]
SOURCE = {"title": "T", "authors": ["Ann Clarke", "Bo Nester"], "year": 2021, "doi": "10.1/x", "licence": "CC BY 4.0"}


@pytest.fixture
def folder(tmp_path):
    (tmp_path / "beats").mkdir()
    (tmp_path / "head.yaml").write_text(yaml.safe_dump({"version": 2, "meta": {"title": "Test comic", "source": SOURCE}, "cast": []}))
    (tmp_path / "beats" / "B1.yaml").write_text(yaml.safe_dump([{"id": "B1", "title": "t", "act": "result", "panels": PANELS}]))
    (tmp_path / "claims.yaml").write_text(yaml.safe_dump({"claims": CLAIMS}))
    return tmp_path


def run(folder, promo):
    promo = {"link": "https://x/y", **promo}
    (folder / "PROMO.yaml").write_text(yaml.safe_dump(promo, allow_unicode=True))
    return CP.check(*CP.load(folder))


def micro(text, claims=("C1",), **kw):
    return {"id": "P1", "kind": "micro", "text": text, "claims": list(claims), **kw}


GOOD = micro("About 40% of reads were assigned to Metazoa in both sample types.")


def test_a_post_that_follows_its_claim_is_clean(folder):
    assert run(folder, {"posts": [GOOD]}) == ([], [])


def test_a_number_no_claim_has_is_an_error(folder):
    e, _ = run(folder, {"posts": [micro("About 45% of reads were assigned to Metazoa.")]})
    assert any("the number 45" in x for x in e)


def test_a_count_in_words_no_claim_has_is_an_error(folder):
    e, _ = run(folder, {"posts": [micro("Three laboratories said about 40% of reads were Metazoa.")]})
    assert any("the count 'three'" in x for x in e)


def test_a_count_in_words_a_claim_has_is_fine(folder):
    assert run(folder, {"posts": [micro("Ten laboratories analysed shared samples; most groups clustered them by ocean region.", ["C2"])]}) == ([], [])


def test_a_claim_that_is_unknown_unverified_or_missing_is_an_error(folder):
    assert any("not in the ledger" in x for x in run(folder, {"posts": [micro("About 40% of reads.", ["C9"])]})[0])
    assert any("not verified" in x for x in run(folder, {"posts": [micro("A claim nobody checked.", ["C3"])]})[0])
    assert any("cites no claim" in x for x in run(folder, {"posts": [micro("About 40% of reads.", [])]})[0])


@pytest.mark.parametrize("text", ["This proves that about 40% of reads were Metazoa.", "A breakthrough: about 40% of reads were Metazoa."])
def test_a_claim_made_stronger_is_an_error(folder, text):
    e, _ = run(folder, {"posts": [micro(text)]})
    assert any("claims more than a paper does" in x for x in e)


@pytest.mark.parametrize("text", ["About 40% of reads were Metazoa. What's your take?", "About 40% of reads were Metazoa. Read on to find out more.",
                                  "About 40% of reads were Metazoa. Agree?"])
def test_engagement_bait_is_an_error(folder, text):
    e, _ = run(folder, {"posts": [micro(text)]})
    assert any("engagement bait" in x for x in e)


def test_the_word_agree_in_a_question_is_not_bait(folder):
    e, _ = run(folder, {"posts": [micro("Where did the groups agree? About 40% of reads were Metazoa.")]})
    assert e == []


def test_a_dropped_hedge_is_a_warning(folder):
    _, w = run(folder, {"posts": [micro("40% of reads were Metazoa in both sample types.")]})
    assert any("the post does not" in x and "hedge" in x for x in w)


def test_a_quantifier_or_absolute_the_claims_lack_is_a_warning(folder):
    _, w = run(folder, {"posts": [micro("Many samples always gave about 40% of reads as Metazoa.")]})
    assert any("'many'" in x for x in w) and any("'always'" in x for x in w)


def test_a_cause_the_claims_lack_is_a_warning(folder):
    _, w = run(folder, {"posts": [micro("About 40% of reads were Metazoa because of the filter.")]})
    assert any("'because'" in x for x in w)


def test_stock_phrases_and_a_pronoun_opener_are_warnings(folder):
    _, w = run(folder, {"posts": [micro("It is not a cheap sample, it is a different one: about 40% of reads. That changes everything.")]})
    assert any("opens with a pronoun" in x for x in w)
    assert any("changes everything" in x for x in w)
    assert any("not" in x and "stock phrase" in x for x in w)


def test_length_limits_count_the_link(folder):
    promo = {"link": "https://x/y", "posts": [micro("About 40% of reads were Metazoa. " + "x" * 230, link=True)]}
    e, _ = run(folder, promo)
    assert any("characters, the limit for a micro post is 280" in x for x in e)
    promo["posts"][0]["text"] = "About 40% of reads were Metazoa. " + "x" * 200
    assert not any("limit" in x for x in run(folder, promo)[0])


def test_a_link_flag_needs_a_link(folder):
    e, _ = run(folder, {"link": None, "posts": [micro("About 40% of reads were Metazoa in both.", link=True)]})
    assert any("no `link`" in x for x in e)


def test_the_abstract_is_100_to_150_words(folder):
    e, _ = run(folder, {"abstract": {"text": "About 40% of reads were Metazoa.", "claims": ["C1"]}})
    assert any("1 words" in x or "words, should be 100 to 150" in x for x in e)
    long_ok = "About 40% of reads were assigned to Metazoa in both sample types. " + "Most groups clustered by ocean region. " * 17
    assert not any("words" in x for x in run(folder, {"abstract": {"text": long_ok, "claims": ["C1", "C2"]}})[0])


def test_a_post_on_a_panel_with_an_unapproved_joke_is_an_error(folder):
    e, _ = run(folder, {"posts": [micro("About 40% of reads were Metazoa.", panel="B1.2")]})
    assert any("joke that is not approved" in x for x in e)
    assert run(folder, {"posts": [micro("About 40% of reads were Metazoa.", panel="B1.1")]})[0] == []
    assert any("does not exist" in x for x in run(folder, {"posts": [micro("About 40% of reads.", panel="B9.9")]})[0])


def test_a_private_comic_is_never_promoted(folder):
    head = yaml.safe_load((folder / "head.yaml").read_text())
    head["meta"]["private"] = True
    (folder / "head.yaml").write_text(yaml.safe_dump(head))
    e, _ = run(folder, {"posts": [GOOD]})
    assert e and "private" in e[0]


def test_a_repeated_text_is_an_error(folder):
    e, _ = run(folder, {"posts": [GOOD, {**GOOD, "id": "P2"}]})
    assert any("the same text" in x for x in e)


def test_a_comic_may_count_its_sources(folder):
    head = yaml.safe_load((folder / "head.yaml").read_text())
    head["meta"] = {"title": "T", "sources": [SOURCE, {**SOURCE, "title": "U"}, {**SOURCE, "title": "V"}]}
    (folder / "head.yaml").write_text(yaml.safe_dump(head))
    assert run(folder, {"headlines": [{"text": "A comic about three studies: about 40% of reads", "claims": ["C1"]}]})[0] == []


def test_write_makes_promo_md_with_evidence_and_credit(folder, capsys):
    (folder / "PROMO.yaml").write_text(yaml.safe_dump({"link": "https://x/y", "posts": [{**GOOD, "link": True, "approved": True}]}))
    assert CP.main([str(folder), "--write"]) == 0
    md = (folder / "PROMO.md").read_text()
    assert "Clarke et al. (2021) doi:10.1/x" in md and "CC BY 4.0" in md
    assert "C1:" in md and "(p. 3)" in md and "https://x/y" in md and "approved" in md


def test_nothing_is_written_when_there_are_errors(folder):
    (folder / "PROMO.yaml").write_text(yaml.safe_dump({"posts": [micro("About 45% of reads.")]}))
    assert CP.main([str(folder), "--write"]) == 1
    assert not (folder / "PROMO.md").exists()


def test_strict_fails_on_an_unapproved_item(folder):
    (folder / "PROMO.yaml").write_text(yaml.safe_dump({"posts": [GOOD]}))
    assert CP.main([str(folder)]) == 0
    assert CP.main([str(folder), "--strict"]) == 1


def test_the_edna_example_text_is_clean():
    assert CP.main([str(ROOT / "examples" / "southern-ocean-edna-agreement")]) == 0
