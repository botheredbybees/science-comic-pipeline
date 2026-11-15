import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import strip_test as S  # noqa: E402

CLAIMS = {
    "C1": {"id": "C1", "text": "Krill ate 41 percent diatoms in the samples."},
    "C2": {"id": "C2", "text": "The 18S libraries were dominated by dinoflagellates, mainly Gyrodinium."},
    "C3": {"id": "C3", "text": "Salps are non-selective filter feeders that ingest particles indiscriminately."},
}


def panel(claim, speech, props=None):
    return {"id": "B1.1", "claim_ids": [claim], "speech": [{"speaker": "narrator", "kind": "caption", "text": t} for t in speech], "staging": {"props": props or []}}


def test_a_number_in_the_words_passes_and_a_number_only_in_a_chart_is_flagged_as_carried_by_the_picture():
    assert S.check_panel(panel("C1", ["Krill ate 41 percent diatoms."]), CLAIMS) == []
    bars = [{"kind": "bars", "bars": [{"label": "diatoms", "value": 41}]}]
    (cid, why), = S.check_panel(panel("C1", ["Krill ate mostly diatoms."], bars), CLAIMS)
    assert cid == "C1" and "41" in why and "chart value" in why


def test_a_number_that_is_part_of_a_name_such_as_18s_is_not_expected_in_the_words():
    assert S.check_panel(panel("C2", ["Libraries were dominated by dinoflagellates, mainly Gyrodinium."]), CLAIMS) == []


def test_a_panel_whose_words_share_almost_no_terms_with_its_claim_is_flagged():
    (cid, why), = S.check_panel(panel("C3", ["Look at that little swimmer go."]), CLAIMS)
    assert cid == "C3" and "terms" in why
    assert S.check_panel(panel("C3", ["Salps ingest particles indiscriminately."]), CLAIMS) == []


def test_words_in_labels_boxes_cards_and_both_halves_of_a_split_count_as_words():
    st = {"props": [{"kind": "box", "label": "boxed words"}, {"kind": "board", "cards": [{"label": "card words"}]}], "split": [{"props": [{"kind": "label", "label": "left words"}]}], "split_labels": ["before"]}
    words, values = S.panel_text({"speech": [], "staging": st})
    assert {"boxed words", "card words", "left words", "before"} <= set(words) and values == []


def test_the_report_lists_flagged_and_silent_panels_and_every_panels_words():
    doc = {"meta": {"title": "T"}, "claims": list(CLAIMS.values()), "beats": [{"id": "B1", "title": "x", "panels": [
        {"id": "B1.1", "claim_ids": ["C3"], "speech": [{"speaker": "narrator", "kind": "caption", "text": "Look at that little swimmer go."}], "staging": {}},
        {"id": "B1.2", "speech": [], "staging": {}}]}]}
    text = S.render(doc, "t.yaml")
    assert "1 flagged" in text and "Panels with no words: B1.2" in text and "Look at that little swimmer go." in text
