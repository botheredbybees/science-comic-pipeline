import os
import shutil
import sys
import time
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import catalogue  # noqa: E402

EXAMPLE = ROOT / "examples" / "akam-2026-cartooning" / "storyboard.yaml"


@pytest.fixture
def repo(tmp_path):
    """A small throwaway repo: one comic with a joke, a renderer stub and a triage table."""
    (tmp_path / "renderers" / "xkcd").mkdir(parents=True)
    (tmp_path / "renderers" / "xkcd" / "render.py").write_text("# renderer\n")
    (tmp_path / "schema").mkdir()
    (tmp_path / "schema" / "storyboard.schema.json").write_text("{}")
    folder = tmp_path / "examples" / "demo"
    folder.mkdir(parents=True)
    doc = yaml.safe_load(EXAMPLE.read_text())
    doc["meta"]["source"]["doi"] = "10.1002/BMB.70040"
    doc["beats"][0]["panels"][0]["humour"] = {"note": "a joke", "keeps_claims_intact": False}
    (folder / "storyboard.yaml").write_text(yaml.safe_dump(doc, sort_keys=False))
    triage = tmp_path / "private" / "triage" / "set"
    triage.mkdir(parents=True)
    (triage / "papers.csv").write_text(
        "file,pages,doi,doi_confirmed,doi_source,title,year,licence,oa_status,class\n"
        "a.pdf,5,10.1002/bmb.70040,yes,,Already a comic,2026,CC BY,gold,usable\n"
        "b.pdf,5,10.1/other,yes,,Not yet a comic,2025,CC BY,gold,usable\n"
        "c.pdf,5,10.1/closed,yes,,Closed paper,2024,,closed,private-only\n")
    (triage / "topics.csv").write_text("category,term,papers,mentions\nequipment,CTD,3,9\n")
    return tmp_path


def q(db, sql, *a):
    return db.execute(sql, a).fetchall()


def test_a_comic_is_catalogued_with_its_checks_and_assets(repo):
    db = catalogue.build(repo)
    slug, loc, private, panels, errors = q(db, "select slug, location, private, panels, errors from comics")[0]
    assert (slug, loc, private, errors) == ("demo", "examples", 0, 0) and panels == 11
    assert q(db, "select uses from comic_assets where kind='prop' and name='bars'")[0][0] >= 1
    assert q(db, "select count(*) from comic_assets where kind='holding'")[0][0] >= 1


def test_pending_jokes_are_listed_until_a_person_confirms_them(repo):
    db = catalogue.build(repo)
    assert q(db, "select panel from jokes where confirmed=0") == [("B1.1",)]
    sb = repo / "examples" / "demo" / "storyboard.yaml"
    doc = yaml.safe_load(sb.read_text())
    doc["beats"][0]["panels"][0]["humour"]["keeps_claims_intact"] = True
    sb.write_text(yaml.safe_dump(doc, sort_keys=False))
    assert q(catalogue.build(repo), "select count(*) from jokes where confirmed=0") == [(0,)]


def test_a_pdf_is_stale_if_missing_or_older_than_the_storyboard_or_the_renderer(repo):
    folder = repo / "examples" / "demo"
    assert q(catalogue.build(repo), "select stale_reason from comics") == [("no PDF",)]
    pdf = folder / "demo.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    now = time.time()
    os.utime(folder / "storyboard.yaml", (now - 100, now - 100))
    os.utime(repo / "renderers" / "xkcd" / "render.py", (now - 100, now - 100))
    os.utime(repo / "schema" / "storyboard.schema.json", (now - 100, now - 100))
    os.utime(pdf, (now, now))
    assert q(catalogue.build(repo), "select stale from comics") == [(0,)]
    os.utime(repo / "renderers" / "xkcd" / "render.py", (now + 50, now + 50))  # the renderer changes
    assert "renderer" in q(catalogue.build(repo), "select stale_reason from comics")[0][0]
    os.utime(repo / "renderers" / "xkcd" / "render.py", (now - 100, now - 100))
    os.utime(folder / "storyboard.yaml", (now + 50, now + 50))  # the storyboard changes
    assert "storyboard" in q(catalogue.build(repo), "select stale_reason from comics")[0][0]


def test_papers_still_to_do_leave_out_comics_already_made_and_closed_papers(repo):
    db = catalogue.build(repo)
    rows = q(db, "select doi from papers p where class='usable' and doi<>'' and doi not in (select doi from comics where doi<>'')")
    assert rows == [("10.1/other",)]  # the comic's DOI matches regardless of case; the closed paper is not usable
    assert q(db, "select term, papers from topics") == [("CTD", 3)]


def test_editions_are_kept_across_rebuilds_and_added_only_for_a_new_pdf(repo):
    folder = repo / "examples" / "demo"
    pdf = folder / "demo.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    os.utime(pdf, (1_700_000_000, 1_700_000_000))
    assert q(catalogue.build(repo), "select count(*) from editions") == [(1,)]
    assert q(catalogue.build(repo), "select count(*) from editions") == [(1,)]  # a rebuild with the same PDF adds nothing
    os.utime(pdf, (1_700_100_000, 1_700_100_000))
    db = catalogue.build(repo)
    assert q(db, "select count(*) from editions where slug='demo'") == [(2,)]  # a new PDF is a new edition


def test_the_command_line_prints_a_summary_and_runs_each_query(repo, capsys):
    for args in ([], ["--stale"], ["--uses", "bars"], ["--pending-jokes"], ["--todo-papers", "5"], ["--editions"], ["--sql", "select 1 as one"]):
        assert catalogue.main(["--root", str(repo)] + args) == 0
    out = capsys.readouterr().out
    assert "1 comic(s)" in out and "Not yet a comic" in out
