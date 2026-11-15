import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "renderers" / "xkcd"))
import review_sheet as RS  # noqa: E402


def test_every_variant_has_a_unique_id_and_the_checklist_names_each_one():
    ids = [pid for pid, *_ in RS.variants()]
    assert len(ids) == len(set(ids)) and len(ids) > 30
    md = RS.checklist()
    assert all(pid in md for pid in ids)
    assert md.count("Verdict:") == sum(len(items) for _, items in RS.ITEMS)


def test_every_asset_kind_in_the_sheet_is_one_the_schema_accepts_and_the_document_validates():
    from validate_storyboard import validate
    doc = RS.build_doc()
    assert [e for e in validate(doc)[0] if e.startswith("schema:")] == []  # the sheet is a catalogue, not a comic, so only the schema is checked (captions carry numbers and cite no claim)


def test_every_new_prop_of_the_last_two_sessions_is_on_the_sheet():
    kinds = {p["kind"] for _, _, _, st in RS.variants() for p in st.get("props", [])}
    assert {"stage", "blackbox", "circle", "hospitalroom", "bridge", "eye", "bookshelf", "spinalcord", "staff", "livingroom", "gears", "ear", "funnel", "brain"} <= kinds
