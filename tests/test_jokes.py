import shutil
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import jokes  # noqa: E402

PAULI = ROOT / "examples" / "pauli-2021-krill-salps-diet"


@pytest.fixture
def repo(tmp_path):
    """A throwaway repo holding a copy of a comic that has beat files, with every joke set to waiting."""
    folder = tmp_path / "examples" / "pauli"
    shutil.copytree(PAULI, folder, ignore=shutil.ignore_patterns("*.pdf"))
    for j in jokes.load_jokes(folder):
        jokes.set_confirmed(folder, j["panel"], False)
    jokes.rebuild(folder)
    return tmp_path


def waiting(repo):
    return [j["panel"] for j in jokes.load_jokes(repo / "examples" / "pauli") if not j["confirmed"]]


def test_edit_flag_changes_only_the_named_panels_flag_and_not_a_longer_id():
    text = ("- id: B1.1\n  humour:\n    keeps_claims_intact: false\n- id: B1.10\n  humour:\n    keeps_claims_intact: false\n")
    new = jokes.edit_flag(text, "B1.1", True)
    assert new.count("keeps_claims_intact: true") == 1 and new.index("true") < new.index("B1.10")
    assert jokes.edit_flag(text, "B9.9", True) is None


def test_list_and_show_give_the_joke_line_the_claims_and_the_questions(repo, capsys):
    assert jokes.main(["list"], root=repo) == 0
    out = capsys.readouterr().out
    assert "I have standards" in out and "2 joke(s) waiting" in out
    jokes.main(["show", "pauli", "B4.5"], root=repo)
    out = capsys.readouterr().out
    assert "CAPTION" in out and "claim C58" in out and "honest to the authors" in out


def test_approving_one_joke_changes_one_line_and_rebuilds_the_storyboard(repo):
    folder = repo / "examples" / "pauli"
    before = {f: f.read_text() for f in folder.rglob("*.yaml")}
    jokes.main(["approve", "pauli", "B4.5"], root=repo)
    changed = [(f, a, b) for f, a in before.items() if (b := f.read_text()) != a]
    assert {f.name for f, _, _ in changed} == {"B4-picky-eaters.yaml", "storyboard.yaml"}
    for _, a, b in changed:
        assert sum(1 for x, y in zip(a.splitlines(), b.splitlines()) if x != y) == 1 and len(a.splitlines()) == len(b.splitlines())
    assert waiting(repo) == ["B6.1"]


def test_approve_all_and_revoke(repo):
    jokes.main(["approve", "pauli", "--all"], root=repo)
    assert waiting(repo) == []
    jokes.main(["revoke", "pauli", "B6.1"], root=repo)
    assert waiting(repo) == ["B6.1"]


def test_cut_removes_the_humour_block_and_the_chosen_line(repo):
    jokes.main(["cut", "pauli", "B4.5", "--line", "3"], root=repo)
    folder = repo / "examples" / "pauli"
    panel = next(p for b in yaml.safe_load((folder / "storyboard.yaml").read_text())["beats"] for p in b["panels"] if p["id"] == "B4.5")
    assert "humour" not in panel and not any("I have standards" in l["text"] for l in panel["speech"])
    assert any(l["text"].startswith("So salps are picky") for l in panel["speech"])  # the question stays


def lines_of(repo, panel):
    folder = repo / "examples" / "pauli"
    p = next(p for b in yaml.safe_load((folder / "storyboard.yaml").read_text())["beats"] for p in b["panels"] if p["id"] == panel)
    return p


def test_review_enter_accepts_and_s_skips(repo, capsys):
    answers = iter(["", "s"])  # an empty answer is the default: accept
    assert jokes.main(["review"], root=repo, ask=lambda prompt: next(answers)) == 0
    assert "1 accepted, 0 edited and accepted, 0 rejected, 1 skipped" in capsys.readouterr().out
    assert waiting(repo) == ["B6.1"]


def test_review_edit_rewords_a_line_then_enter_accepts_the_edited_joke(repo, capsys):
    answers = iter(["e", "", "I am particular.", "", "q"])  # edit (default line), new text, then accept, then quit at the next joke
    jokes.main(["review"], root=repo, ask=lambda prompt: next(answers))
    out = capsys.readouterr().out
    assert "1 edited and accepted" in out
    panel = lines_of(repo, "B4.5")
    assert panel["humour"]["keeps_claims_intact"] is True
    assert [l["text"] for l in panel["speech"]][-1] == "I am particular."
    assert any(l["text"].startswith("So salps are picky") for l in panel["speech"])  # the question is untouched


def test_review_reject_deletes_the_last_character_line_by_default_or_keeps_the_lines(repo):
    answers = iter(["r", "", "r", "keep"])  # B4.5: delete the default line; B6.1: keep the line, drop the joke flag only
    jokes.main(["review"], root=repo, ask=lambda prompt: next(answers))
    first = lines_of(repo, "B4.5")
    assert "humour" not in first and not any("I have standards" in l["text"] for l in first["speech"])
    second = lines_of(repo, "B6.1")
    assert "humour" not in second and any("Don't look at me" in l["text"] for l in second["speech"])
    assert waiting(repo) == []


def test_edit_changes_one_line_in_place_when_the_text_is_plain_and_falls_back_when_it_is_not(repo):
    folder = repo / "examples" / "pauli"
    beat = next(folder.glob("beats/B4-*.yaml"))
    before = beat.read_text().splitlines()
    jokes.main(["edit", "pauli", "B4.5", "--line", "3", "--text", "I am particular."], root=repo)
    after = beat.read_text().splitlines()
    assert len(after) == len(before) and sum(1 for a, b in zip(before, after) if a != b) == 1  # one line, nothing re-flowed
    jokes.main(["edit", "pauli", "B4.5", "--line", "3", "--text", "Don't ask: I'm picky."], root=repo)  # a colon and quotes need the fallback
    assert lines_of(repo, "B4.5")["speech"][2]["text"] == "Don't ask: I'm picky."
    jokes.main(["edit", "pauli", "B4.5", "--note", "--text", "A new note."], root=repo)
    assert lines_of(repo, "B4.5")["humour"]["note"] == "A new note."


def test_a_comic_name_must_match_exactly_one(repo):
    with pytest.raises(SystemExit):
        jokes.pick(repo, "nothing-like-this")
