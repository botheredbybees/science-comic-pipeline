import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_storyboard import build, main  # noqa: E402


def claim(cid, status="verified"):
    return {"id": cid, "text": "t", "kind": "background", "status": status, "source": {"locator": "x"}}


def folder(tmp_path, claims, beats):
    (tmp_path / "beats").mkdir()
    (tmp_path / "head.yaml").write_text(yaml.safe_dump({"version": 2, "meta": {"title": "T"}, "cast": []}))
    (tmp_path / "claims.yaml").write_text(yaml.safe_dump({"claims": claims}))
    (tmp_path / "beats" / "B1.yaml").write_text(yaml.safe_dump(beats))
    return tmp_path


BEATS = [{"id": "B1", "act": "problem", "panels": [{"id": "B1.1", "scene": "s", "claim_ids": ["C2"]}]}]


def test_only_cited_claims_are_kept(tmp_path):
    doc, unverified, n = build(folder(tmp_path, [claim("C1"), claim("C2")], BEATS))
    assert [c["id"] for c in doc["claims"]] == ["C2"] and n == 2 and unverified == []


def test_unverified_cited_claims_are_reported(tmp_path):
    _, unverified, _ = build(folder(tmp_path, [claim("C2", "unverified")], BEATS))
    assert unverified == ["C2"]


def test_a_cited_claim_missing_from_the_ledger_is_an_error(tmp_path):
    with pytest.raises(ValueError, match="not in any ledger"):
        build(folder(tmp_path, [claim("C1")], BEATS))


def test_a_claim_in_two_ledgers_is_an_error(tmp_path):
    f = folder(tmp_path, [claim("C2")], BEATS)
    (f / "claims-b.yaml").write_text(yaml.safe_dump({"claims": [claim("C2")]}))
    with pytest.raises(ValueError, match="more than one"):
        build(f)


def test_cli_writes_storyboard_yaml(tmp_path):
    f = folder(tmp_path, [claim("C2")], BEATS)
    assert main([str(f)]) == 0 and (f / "storyboard.yaml").exists()
