import copy
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from validate_storyboard import main, validate, variety  # noqa: E402

EXAMPLE = ROOT / "examples" / "akam-2026-cartooning" / "storyboard.yaml"


@pytest.fixture
def doc():
    return yaml.safe_load(EXAMPLE.read_text())


def test_example_has_no_errors(doc):
    errors, _ = validate(doc)
    assert errors == []


def test_example_is_fully_verified_and_clean(doc):
    errors, warnings = validate(doc)
    assert errors == [] and warnings == []


def test_abstract_only_claim_drawn_in_a_panel_is_a_warning(doc):
    doc["claims"][0]["status"] = "abstract_only"
    _, warnings = validate(doc)
    assert any("C1 is abstract_only" in w for w in warnings)


def test_unknown_speaker_is_an_error(doc):
    doc["beats"][0]["panels"][0]["speech"][0]["speaker"] = "nobody"
    errors, _ = validate(doc)
    assert any("'nobody' is not in the cast" in e for e in errors)


def test_unknown_claim_is_an_error(doc):
    doc["beats"][0]["panels"][0]["claim_ids"] = ["C99"]
    errors, _ = validate(doc)
    assert any("unknown claim C99" in e for e in errors)


def test_number_without_claim_is_an_error(doc):
    panel = doc["beats"][0]["panels"][0]
    panel["claim_ids"] = []
    panel["speech"] = [{"speaker": "narrator", "text": "Seventy-nine, no, 79 students."}]
    errors, _ = validate(doc)
    assert any("contain a number but the panel cites no claim" in e for e in errors)


def test_unused_claim_is_a_warning(doc):
    doc["claims"].append(
        {"id": "C98", "text": "Spare.", "kind": "background", "source": {"locator": "abstract"}, "status": "verified"}
    )
    errors, warnings = validate(doc)
    assert errors == []
    assert any("C98 is in the ledger but no panel uses it" in w for w in warnings)


def test_joke_on_cited_panel_is_a_warning_until_reviewed(doc):
    panel = doc["beats"][0]["panels"][0]
    panel["claim_ids"] = ["C1"]
    panel["humour"] = {"note": "deadpan"}
    _, warnings = validate(doc)
    assert any("joke on a panel that cites C1" in w for w in warnings)
    panel["humour"]["keeps_claims_intact"] = True
    _, warnings = validate(doc)
    assert not any("joke on a panel that cites C1" in w for w in warnings)


def test_duplicate_ids_are_errors(doc):
    doc["cast"].append(copy.deepcopy(doc["cast"][0]))
    errors, _ = validate(doc)
    assert any("duplicate cast id" in e for e in errors)


def test_first_panel_cannot_have_a_transition(doc):
    doc["beats"][0]["panels"][0]["transition"] = "scene-to-scene"
    errors, _ = validate(doc)
    assert any("first panel has a transition" in e for e in errors)


def test_panel_id_must_belong_to_its_beat(doc):
    doc["beats"][0]["panels"][1]["id"] = "B2.9"
    errors, _ = validate(doc)
    assert any("does not belong to beat B1" in e for e in errors)


def test_unknown_weight_transition_and_mode_are_schema_errors(doc):
    panel = doc["beats"][0]["panels"][1]
    panel["weight"], panel["transition"], panel["word_picture"] = "huge", "teleport", "loud"
    errors, _ = validate(doc)
    assert len([e for e in errors if e.startswith("schema:")]) == 3


def test_no_limit_on_panel_count(doc):
    template = doc["beats"][0]["panels"][1]
    doc["beats"].append({"id": "B9", "act": "result", "panels": [
        {**template, "id": f"B9.{i}", "claim_ids": ["C2"]} for i in range(1, 201)]})
    errors, _ = validate(doc)
    assert errors == []


def test_pages_are_no_longer_accepted(doc):
    doc["pages"] = []
    errors, _ = validate(doc)
    assert any("pages" in e for e in errors)


def test_schema_error_stops_other_checks(doc):
    del doc["meta"]["spine"]
    errors, _ = validate(doc)
    assert errors and all(e.startswith("schema:") for e in errors)


def test_cli_exit_codes(tmp_path, capsys):
    assert main([str(EXAMPLE)]) == 0
    assert main([str(EXAMPLE), "--strict"]) == 0  # the example is clean
    warned = yaml.safe_load(EXAMPLE.read_text())
    warned["claims"][0]["status"] = "unverified"
    path = tmp_path / "warned.yaml"
    path.write_text(yaml.safe_dump(warned))
    assert main([str(path)]) == 0
    assert main([str(path), "--strict"]) == 1
    bad = tmp_path / "bad.yaml"
    bad.write_text("version: 1\n")
    assert main([str(bad)]) == 1


def test_chart_numbers_need_a_claim(doc):
    panel = next(p for b in doc["beats"] for p in b["panels"] if p["id"] == "B3.1")
    panel["claim_ids"] = []
    panel["speech"] = []
    errors, _ = validate(doc)
    assert any("B3.1" in e and "contain a number" in e for e in errors)


def test_chart_values_hidden_from_view_need_no_claim(doc):
    panel = next(p for b in doc["beats"] for p in b["panels"] if p["id"] == "B3.3")
    panel["claim_ids"], panel["speech"] = [], []
    errors, _ = validate(doc)
    assert not any("B3.3" in e for e in errors)


def test_staged_character_must_be_in_the_cast_or_extra(doc):
    doc["beats"][0]["panels"][0]["staging"]["characters"].append({"id": "ghost"})
    errors, _ = validate(doc)
    assert any("staged character 'ghost' is not in the cast" in e for e in errors)


def test_speaker_missing_from_staging_is_a_warning(doc):
    doc["beats"][0]["panels"][0]["staging"]["characters"] = []
    _, warnings = validate(doc)
    assert any("sam speaks but is not in the staging" in w for w in warnings)


def test_unknown_prop_kind_is_a_schema_error(doc):
    doc["beats"][0]["panels"][0]["staging"]["props"][0]["kind"] = "spaceship"
    errors, _ = validate(doc)
    assert any(e.startswith("schema:") for e in errors)


def _with_chart(doc, show_max):
    panel = copy.deepcopy(next(p for b in doc["beats"] for p in b["panels"] if p["id"] == "B3.1"))
    panel["claim_ids"], panel["speech"] = [], []
    panel["staging"] = {"props": [{"kind": "bars", "max": 520, "show_max": show_max, "bars": [{"label": "low", "value": 5, "style": "hollow"}], "show_values": False}]}
    doc["beats"] = [{"id": "B1", "act": "result", "panels": [{**panel, "id": "B1.1"}]}]
    doc["claims"] = []
    return validate(doc)


def test_a_visible_axis_maximum_is_a_number_that_needs_a_claim(doc):
    # show_values False hides the maximum too, so nothing is printed and nothing needs a claim
    errors, _ = _with_chart(doc, True)
    assert not any("contain a number" in e for e in errors)


def test_the_axis_maximum_counts_as_printed_text_only_when_it_is_shown():
    from validate_storyboard import _staging_texts
    bars = {"kind": "bars", "max": 520, "bars": [{"label": "x", "value": 5}]}
    assert "520" in _staging_texts({"props": [bars]})
    assert "520" not in _staging_texts({"props": [{**bars, "show_max": False}]})
    assert "520" not in _staging_texts({"props": [{**bars, "show_values": False}]})


def test_a_number_not_in_any_cited_claim_is_a_warning(doc):
    panel = doc["beats"][0]["panels"][0]
    panel["claim_ids"] = ["C1"]
    panel["speech"] = [{"speaker": "narrator", "kind": "caption", "text": "In 1999 and 77 cases."}]
    _, warnings = validate(doc)
    assert any("B1.1" in w and "appear on the panel but in none of its cited claims" in w for w in warnings)


def test_numbers_that_come_from_the_cited_claims_do_not_warn(doc):
    _, warnings = validate(doc)
    assert not any("none of its cited claims" in w for w in warnings)


def test_scene_naming_an_unstaged_prop_warns_and_a_joke_on_a_claim_free_panel_warns(doc):
    panel = doc["beats"][0]["panels"][0]
    panel["scene"] = "Ines stands at a desk."
    panel["staging"] = {"characters": [{"id": "extra", "x": 0.5}]}
    panel["claim_ids"] = []
    for line in panel.get("speech", []):
        line["text"] = "No numbers here."
    panel["humour"] = {"note": "a joke", "keeps_claims_intact": False}
    errors, warnings = validate(doc)
    assert any("mentions a desk" in w for w in warnings)
    assert any("joke on a panel that cites no claim" in w for w in warnings)
    panel["staging"]["props"] = [{"kind": "desk"}]
    assert not any("mentions a desk" in w for w in validate(doc)[1])


def _panel(doc):
    return doc["beats"][0]["panels"][0]


def test_thousands_separators_match_a_chart_value(doc):
    doc["claims"][0]["text"] = "There were 55, 465 specimens in total."
    p = _panel(doc)
    p["claim_ids"] = ["C1"]
    p["speech"] = [{"speaker": "narrator", "text": "There were 55,465 specimens."}]
    p["staging"] = {"props": [{"kind": "bars", "bars": [{"label": "all", "value": 55465}], "max": 60000, "show_max": False}]}
    _, warnings = validate(doc)
    assert not any("55465" in w or "465" in w for w in warnings if _panel(doc)["id"] in w)


def test_scene_naming_a_held_object_nobody_holds_warns(doc):
    p = _panel(doc)
    p["scene"] = "Dr Okoye lowers the mug."
    p["staging"] = {"characters": [{"id": "extra"}]}
    _, warnings = validate(doc)
    assert any("mug but nobody in the staging holds one" in w for w in warnings)
    p["staging"] = {"characters": [{"id": "extra", "holding": "mug"}]}
    _, warnings = validate(doc)
    assert not any("mug but nobody" in w for w in warnings)


def test_scene_words_that_are_not_objects_do_not_warn(doc):
    p = _panel(doc)
    p["scene"] = "They discuss the jar water samples and the microscope work."
    _, warnings = validate(doc)
    assert not any("the scene (the alt text) mentions" in w and p["id"] in w for w in warnings)


def test_board_with_long_labels_warns_and_short_ones_do_not(doc):
    p = _panel(doc)
    p["staging"] = {"props": [{"kind": "board", "cards": [{"label": "A"}, {"label": "B"}, {"label": "C"}, {"label": "D"}]}]}
    _, warnings = validate(doc)
    assert not any("board with long labels" in w for w in warnings)
    p["staging"]["props"][0]["cards"][0]["label"] = "A whole clause that will not fit on a card"
    _, warnings = validate(doc)
    assert any("board with long labels" in w for w in warnings)


def test_a_speaking_extra_gets_a_helpful_error(doc):
    _panel(doc)["speech"][0]["speaker"] = "extra"
    errors, _ = validate(doc)
    assert any("needs a cast entry" in e for e in errors)


def test_a_comic_of_mostly_bare_stick_figures_warns_and_a_picture_comic_does_not(doc):
    _, warnings = validate(doc)
    assert not any("show only stick figures" in w for w in warnings)
    d = copy.deepcopy(doc)
    for b in d["beats"]:
        for p in b["panels"]:
            p["staging"] = {"characters": [{"id": "extra"}]}
    _, warnings = validate(d)
    assert any("show only stick figures" in w for w in warnings)


def test_an_animal_or_a_prop_counts_as_a_picture(doc):
    d = copy.deepcopy(doc)
    for b in d["beats"]:
        for p in b["panels"]:
            p["staging"] = {"characters": [{"id": "extra", "body": "copepod"}]}
    _, warnings = validate(d)
    assert not any("show only stick figures" in w for w in warnings)


def test_strand_hair_on_a_bun_warns(doc):
    doc["cast"][0]["appearance"] = {"hair": "bun", "hair_tone": "strands"}
    _, warnings = validate(doc)
    assert any("strand hair on a bun" in w for w in warnings)
    doc["cast"][0]["appearance"] = {"hair": "long", "hair_tone": "strands"}
    _, warnings = validate(doc)
    assert not any("strand hair on a bun" in w for w in warnings)


def test_a_lab_coat_and_an_outfit_together_warn(doc):
    doc["cast"][0]["appearance"] = {"coat": True, "outfit": "parka"}
    _, warnings = validate(doc)
    assert any("only the outfit is drawn" in w for w in warnings)


def _long_comic(doc, transition="scene-to-scene", n=24):
    """The example stretched to n panels, every one with the same transition and no word-picture label or device."""
    d = copy.deepcopy(doc)
    first = d["beats"][0]["panels"][0]
    d["beats"] = [{"id": "B1", "title": "t", "act": "problem", "panels": [
        {**copy.deepcopy(first), "id": f"B1.{i}", "transition": transition, "word_picture": None} for i in range(1, n + 1)]}]
    for p in d["beats"][0]["panels"]:
        p.pop("word_picture", None)
        p.pop("humour", None)
        p.pop("device", None)
    d["beats"][0]["panels"][0].pop("transition", None)  # the first panel follows nothing
    return d


def test_a_monotonous_long_comic_is_flagged_for_variety_and_a_short_one_is_not(doc):
    stats, warnings = variety(_long_comic(doc))
    text = " ".join(warnings)
    assert stats["scene_pct"] == 100 and "scene-to-scene" in text and "moment-to-moment" in text and "word_picture" in text and "gloss" in text
    assert variety(doc)[1] == []  # the 11-panel example is below the threshold


def test_variety_is_satisfied_by_a_varied_comic(doc):
    d = _long_comic(doc, "action-to-action")
    kinds = ["moment-to-moment", "aspect-to-aspect", "subject-to-subject", "action-to-action"]
    for i, p in enumerate(d["beats"][0]["panels"]):
        p["transition"] = kinds[i % 4]
        p["word_picture"] = "picture-specific" if i % 5 == 0 else "additive"
    d["beats"][0]["panels"][3]["device"] = "gloss"
    d["beats"][0]["panels"][3]["claim_ids"] = ["C1"]
    d["beats"][0]["panels"][3]["speech"].append({"speaker": "sam", "text": "In other words, plain English."})
    d["beats"][0]["panels"][7]["device"] = "moment"
    assert variety(d)[1] == []


def test_a_gloss_must_cite_a_claim_and_have_a_character_line(doc):
    d = _long_comic(doc)
    p = d["beats"][0]["panels"][0]
    p.update(device="gloss", claim_ids=[])
    p["speech"] = [l for l in p["speech"] if l.get("kind") == "caption"]
    text = " ".join(variety(d)[1])
    assert "must cite the definition claim" in text and "has none" in text


def _first_panel(doc):
    return doc["beats"][0]["panels"][0]


def test_a_label_that_only_says_schematic_or_stand_in_warns(doc):
    p = _first_panel(doc)
    p["staging"] = {"props": [{"kind": "tubes", "x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5, "label": "schematic"},
                              {"kind": "label", "x": 0.1, "y": 0.8, "label": "stand-ins, not to scale"}]}
    text = " ".join(validate(doc)[1])
    assert "'schematic' repeats what the footer already says" in text and "'stand-ins, not to scale' repeats" in text


def test_a_bracketed_stand_in_on_a_real_label_also_warns_but_a_plain_name_does_not(doc):
    p = _first_panel(doc)
    p["staging"] = {"props": [{"kind": "rmt", "x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5, "label": "mid-water trawl (schematic)"}]}
    assert any("repeats what the footer" in w for w in validate(doc)[1])
    p["staging"]["props"][0]["label"] = "mid-water trawl"
    assert not any("repeats what the footer" in w for w in validate(doc)[1])


def test_a_panel_with_no_words_but_a_boilerplate_label_is_a_filler(doc):
    p = _first_panel(doc)
    p.pop("speech", None)
    p.pop("humour", None)
    p["staging"] = {"props": [{"kind": "filter", "x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8, "label": "schematic"}]}
    assert any(f"{p['id']}: the panel has no caption, speech or label" in w for w in validate(doc)[1])
    p["staging"]["props"][0]["label"] = "water filter"  # a label that names the thing is words
    assert not any("has no caption, speech or label" in w for w in validate(doc)[1])


def test_a_silent_panel_is_allowed_when_it_is_a_joke(doc):
    p = _first_panel(doc)
    p.pop("speech", None)
    p["humour"] = {"note": "a silent beat", "keeps_claims_intact": True}
    assert not any("has no caption, speech or label" in w for w in validate(doc)[1])


def test_a_wordless_panel_does_not_count_as_a_moment(doc):
    d = _long_comic(doc, "moment-to-moment")
    for p in d["beats"][0]["panels"]:
        p["speech"] = []
        p["staging"] = {"props": [{"kind": "filter", "x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8, "label": "schematic"}]}
    assert variety(d)[0]["moment_pct"] == 0


def test_the_variety_flag_prints_a_report_without_changing_the_default(doc, tmp_path, capsys):
    f = tmp_path / "s.yaml"
    f.write_text(yaml.safe_dump(_long_comic(doc), sort_keys=False))
    assert main([str(f)]) in (0, 1)
    assert "variety:" not in capsys.readouterr().out
    main([str(f), "--variety"])
    assert "variety:" in capsys.readouterr().out


def _topic(doc):
    d = copy.deepcopy(doc)
    src = d["meta"].pop("source")
    d["meta"]["sources"] = [{"id": "one", **src}, {"id": "two", **src}]
    for c in d["claims"]:
        c["source"]["ref"] = "one"
    return d


def test_a_topic_comic_validates_when_every_claim_names_its_paper(doc):
    errors, _ = validate(_topic(doc))
    assert errors == []


def test_a_topic_comic_claim_needs_a_known_ref(doc):
    d = _topic(doc)
    d["claims"][0]["source"]["ref"] = "three"
    del d["claims"][1]["source"]["ref"]
    errors, _ = validate(d)
    assert any("'three' is not in meta.sources" in e for e in errors)
    assert any("needs a `ref`" in e for e in errors)


def test_a_one_paper_comic_does_not_use_ref_and_the_two_forms_do_not_mix(doc):
    d = copy.deepcopy(doc)
    d["claims"][0]["source"]["ref"] = "x"
    assert any("only for comics with meta.sources" in e for e in validate(d)[0])
    both = _topic(doc)
    both["meta"]["source"] = {"title": "s", "authors": ["a"], "year": 2026, "licence": "x"}
    assert any("both `source` and `sources`" in e for e in validate(both)[0])


def test_argument_and_practice_are_claim_kinds(doc):
    d = copy.deepcopy(doc)
    d["claims"][0]["kind"], d["claims"][1]["kind"] = "argument", "practice"
    assert validate(d)[0] == []


def test_a_net_labelled_cpr_is_a_warning(doc):
    d = copy.deepcopy(doc)
    p = d["beats"][0]["panels"][0]
    p.setdefault("staging", {}).setdefault("props", []).append({"kind": "net", "x": 0.5, "y": 0.1, "w": 0.2, "h": 0.5, "label": "CPR"})
    _, warnings = validate(d)
    assert any("use the `cpr` prop" in w for w in warnings)
    p["staging"]["props"][-1]["kind"] = "cpr"
    assert not any("use the `cpr` prop" in w for w in validate(d)[1])
