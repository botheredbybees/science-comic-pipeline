import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import select_key_cards as sk  # noqa: E402


def cards(n=30):
    kinds = ["background", "method", "result", "caveat", "future_research", "interpretation"]
    return [{"id": f"C{i}", "text": f"claim {i}", "kind": kinds[i % 6], "source": {"page": i, "quote": "q"}} for i in range(1, n + 1)]


def ask_with(key=(), individuals=()):
    """A fake model: answers the question about individuals or the key-card question, whichever the prompt asks."""
    def ask(prompt):
        return json.dumps({"individuals": list(individuals)} if "ONE specific person" in prompt else {"key": list(key)})
    return ask


def test_the_models_choices_are_kept_and_nonexistent_ids_are_discarded():
    res = sk.select(cards(), ask_with(["C2", "C3", "C4", "C5", "C6", "C7", "C99"], ["C14", "C98"]), n=10)  # C14 is a result
    assert res["key"] == ["C2", "C3", "C4", "C5", "C6", "C7"] and res["omit"] == ["C14"]


def test_a_card_cannot_be_both_key_and_omitted():
    res = sk.select(cards(), ask_with(["C14", "C4", "C5", "C6", "C7", "C8"], ["C14"]), n=10)  # C14 is a result
    assert "C14" not in res["key"] and "C14" in res["omit"]


def test_methods_caveats_and_calls_for_research_are_never_left_off():
    cs = cards()
    kinds = {c["id"]: c["kind"] for c in cs}
    res = sk.select(cs, ask_with(["C2", "C3", "C4", "C5", "C6", "C7"], [i for i in kinds]), n=10)
    assert all(kinds[i] not in ("method", "caveat", "future_research") for i in res["omit"])


def test_the_two_questions_are_asked_separately():
    prompts = []

    def ask(prompt):
        prompts.append(prompt)
        return json.dumps({"individuals": []} if "ONE specific person" in prompt else {"key": ["C2", "C3", "C4", "C5", "C6", "C7"]})
    sk.select(cards(), ask, n=10)
    assert len(prompts) == 2 and sum("ONE specific person" in p for p in prompts) == 1


def test_too_few_choices_are_filled_by_kind_and_results_come_first():
    res = sk.select(cards(), ask_with(), n=10)
    assert len(res["key"]) >= 6
    assert {c["kind"] for c in cards() if c["id"] in res["key"]} >= {"result", "method"}


def test_flagged_cards_are_never_offered_or_chosen():
    cs = cards()
    cs[2]["model_check"] = {"verdict": "overstated"}  # C3
    seen = []

    def ask(prompt):
        seen.append(prompt)
        return json.dumps({"key": ["C3", "C4", "C5", "C6", "C7", "C8"]})
    res = sk.select(cs, ask, n=10)
    assert all("C3 [" not in p for p in seen) and "C3" not in res["key"]


def test_a_reply_that_is_not_json_still_gives_a_usable_selection():
    res = sk.select(cards(), lambda p: "sorry", n=10)
    assert len(res["key"]) >= 6 and res["omit"] == []
