import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import suggest_graphics as sg  # noqa: E402

CARDS = [
    {"id": "C1", "text": "The program has run since 2010.", "kind": "background", "source": {"page": 6, "quote": "since 2010"}},
    {"id": "C2", "text": "Twenty-four participants completed the study.", "kind": "method", "source": {"page": 4, "quote": "24 participants"}},
    {"id": "C3", "text": "A sceptical claim.", "kind": "result", "source": {"page": 5, "quote": "q"}, "model_check": {"verdict": "overstated"}},
]
VOCAB = {"axis": "a timeline", "bars": "amounts", "armchair": "a care home"}


def g(**kw):
    base = {"title": "T", "shows": "s", "claim_ids": ["C1"], "element": {"kind": "axis", "values": []}}
    base.update(kw)
    return base


def test_the_vocabulary_comes_from_the_schema_and_leaves_out_polar_apparatus():
    v = sg.vocabulary()
    assert "bars" in v and "venn" in v and "armchair" in v
    assert "cpr" not in v and "bongo" not in v


def test_a_good_suggestion_is_kept():
    kept, rej = sg.validate([g()], CARDS, VOCAB)
    assert len(kept) == 1 and not rej


def test_an_unknown_element_kind_is_rejected_but_new_with_a_name_is_kept():
    _, rej = sg.validate([g(element={"kind": "spaceship"})], CARDS, VOCAB)
    assert "not one of the renderer's props" in rej[0]["rejected_because"]
    kept, _ = sg.validate([g(element={"kind": "new"}, new_asset="gallery wall")], CARDS, VOCAB)
    assert kept
    _, rej = sg.validate([g(element={"kind": "new"})], CARDS, VOCAB)
    assert "missing drawing is not named" in rej[0]["rejected_because"]


def test_a_suggestion_must_cite_real_cards():
    assert "cites no card" in sg.validate([g(claim_ids=[])], CARDS, VOCAB)[1][0]["rejected_because"]
    assert "does not exist: C99" in sg.validate([g(claim_ids=["C1", "C99"])], CARDS, VOCAB)[1][0]["rejected_because"]


def test_a_chart_value_must_appear_in_a_cited_card():
    ok = g(claim_ids=["C2"], element={"kind": "bars", "values": [{"label": "participants", "value": 24}]})
    bad = g(claim_ids=["C2"], element={"kind": "bars", "values": [{"label": "participants", "value": 99}]})
    kept, rej = sg.validate([ok, bad], CARDS, VOCAB)
    assert len(kept) == 1 and "99" in rej[0]["rejected_because"]


def test_suggest_leaves_flagged_cards_out_of_the_prompt_and_drops_bad_replies():
    seen = {}

    def ask(prompt):
        seen["p"] = prompt
        return json.dumps({"graphics": [g(), g(claim_ids=["C3"])]})  # C3 was flagged, so it is not a card the model may cite
    kept, rejected = sg.suggest(CARDS, ask, VOCAB)
    assert "C3" not in seen["p"].split("Cards:")[1] and len(kept) == 1 and len(rejected) == 1


def test_a_truncated_reply_is_salvaged():
    text = json.dumps({"graphics": [g(), g(title="U")]})
    truncated = text[:text.index('"title": "U"') + 14]  # the reply stops in the middle of the second suggestion
    assert [x["title"] for x in sg.parse(truncated)] == ["T"]


def test_the_rollup_counts_existing_elements_and_groups_similar_missing_ones(tmp_path):
    for i, assets in enumerate((["gallery wall with paintings"], ["gallery wall with framed paintings", "tea table"], ["tea table"])):
        d = tmp_path / f"p{i}"
        d.mkdir()
        gl = [g(element={"kind": "new"}, new_asset=a) for a in assets] + [g()]
        (d / "graphics.yaml").write_text(yaml.safe_dump({"paper": f"p{i}", "graphics": gl}))
    text = sg.rollup(sorted(str(p) for p in tmp_path.glob("*/graphics.yaml")))
    assert "`axis`: 3" in text
    assert "tea table**: 2 papers" in text and "gallery wall with paintings**: 2 papers" in text


def test_number_words_count_as_numbers_in_a_card():
    assert {"8", "24", "20", "2"} <= sg.numbers_in("Eight pairs; twenty-four people; twenty; two")
    ok = g(claim_ids=["C2"], element={"kind": "bars", "values": [{"label": "completed", "value": 24}]})  # the card says "Twenty-four"
    assert sg.validate([ok], CARDS, VOCAB)[0]


def test_a_data_chart_with_no_number_behind_it_is_rejected():
    empty = g(claim_ids=["C2"], element={"kind": "bars", "values": []})
    given = g(claim_ids=["C2"], element={"kind": "bars", "values": [{"label": "completed", "value": 24}]})
    kept, rej = sg.validate([empty, given], CARDS, VOCAB)
    assert len(kept) == 1 and "draws values" in rej[0]["rejected_because"]
    assert sg.validate([g(element={"kind": "axis", "values": []})], CARDS, VOCAB)[0]  # a timeline needs no values


def test_missing_assets_are_grouped_by_the_word_they_share():
    names = ["gallery wall with framed paintings", "accessible gallery interior with ramps", "cross-section of a gallery room", "hand holding a flower",
             "two hands placing a photo", "a unique one-off thing"]
    themes = dict(sg.gap_themes(names))
    assert len(themes["gallery"]) == 3 and len(themes["hand"]) == 2
    assert not any("unique" in n for ns in themes.values() for n in ns)  # a word only one request uses is not a theme
