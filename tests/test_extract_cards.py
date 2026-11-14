import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_quotes import contains_quote  # noqa: E402
from extract_cards import extract, parse_claims, windows  # noqa: E402

PAGES = {1: "Public health improved in four waves since the Industrial Revolution, each answering the needs of its time.",
         2: "The authors say further research is needed on how the arts can be integrated into public health systems everywhere."}


def fake(claims):
    return lambda prompt: json.dumps({"claims": claims})


def test_exact_snapped_and_invented_quotes_are_counted_and_only_real_text_is_kept():
    reply = [
        {"page": 1, "quote": "Public health improved in four waves since the Industrial Revolution", "kind": "background", "paraphrase": "Four waves."},
        {"page": 2, "quote": "further research is needed on how the arts can be integrated into public health systems", "kind": "future_research", "paraphrase": "More research."},
        {"page": 1, "quote": "Public health improved in four waves since the industrial revolution, every one meeting the needs of its time", "kind": "background", "paraphrase": "Waves."},
        {"page": 1, "quote": "The moon is made of green cheese and every wave arrived on a Tuesday", "kind": "background", "paraphrase": "Invented."},
    ]
    cards, stats = extract(PAGES, "x-2020", fake(reply))
    assert len(cards) == 2 and stats["dropped"] == 1 and stats["duplicate"] == 1
    assert all(contains_quote(PAGES[c["source"]["page"]], c["source"]["quote"]) for c in cards)
    assert {c["status"] for c in cards} == {"unverified"} and [c["id"] for c in cards] == ["C1", "C2"]
    assert cards[1]["kind"] == "future_research"


def test_a_cut_off_reply_keeps_its_complete_entries():
    text = '{"claims": [{"page": 1, "quote": "a b c d e f g h", "kind": "result", "paraphrase": "x"}, {"page": 2, "quote": "unfinished'
    assert len(parse_claims(text)) == 1


def test_long_documents_are_read_in_overlapping_windows():
    pages = {n: "word " * 6000 for n in range(1, 7)}
    ws = windows(pages)
    assert len(ws) > 1 and ws[0][-1] == ws[1][0]


def test_verify_adds_a_verdict_to_every_card_and_defaults_to_unclear():
    from verify_cards import verify
    cards = [{"id": "C1", "text": "a", "source": {"quote": "q"}}, {"id": "C2", "text": "b", "source": {"quote": "r"}}]
    counts = verify(cards, lambda p: json.dumps({"verdicts": [{"id": "C1", "verdict": "supported", "why": "ok"}]}))
    assert cards[0]["model_check"]["verdict"] == "supported" and cards[1]["model_check"]["verdict"] == "unclear"
    assert counts == {"supported": 1, "unclear": 1}
