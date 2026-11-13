import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from triage_papers import classify, confirmed, count_terms, find_doi, main  # noqa: E402


def test_find_doi_takes_the_first_one_and_drops_trailing_punctuation():
    assert find_doi("Published online. DOI: 10.1111/mec.15587. Received 2020") == "10.1111/mec.15587"
    assert find_doi("see https://doi.org/10.3389/fmicb.2018.03226), and 10.1/x") == "10.3389/fmicb.2018.03226"
    assert find_doi("no identifier here") == ""


def test_a_doi_is_confirmed_only_when_the_title_is_on_the_first_page():
    page = "Capturing open ocean biodiversity: Comparing environmental DNA metabarcoding to the continuous plankton recorder"
    assert confirmed("Capturing open ocean biodiversity: Comparing environmental DNA metabarcoding to the continuous plankton recorder", page)
    assert not confirmed("Bacterial epibiont communities of panmictic Antarctic krill are spatially structured", page)
    assert not confirmed("Short title", page)  # too few words to judge


def test_classify_by_crossref_licence_and_unpaywall():
    assert classify(["http://creativecommons.org/licenses/by/4.0/"], {}, "10.1/x") == ("CC BY", "usable")
    assert classify(["https://creativecommons.org/licenses/by-sa/4.0/"], {}, "10.1/x") == ("CC BY-SA", "usable")
    assert classify(["https://creativecommons.org/licenses/by-nc-nd/4.0/"], {}, "10.1/x") == ("CC BY-NC-ND", "private-only")
    assert classify(["https://www.elsevier.com/tdm/userlicense/1.0/"], {}, "10.1/x")[1] == "private-only"
    assert classify([], {"is_oa": True, "best_oa_location": {"license": "cc-by"}}, "10.1/x")[1] == "usable"
    assert classify([], {"is_oa": True, "best_oa_location": {}}, "10.1/x")[1] == "check"
    assert classify([], {}, "") == ("", "no-doi")


def test_terms_are_counted_case_sensitively_for_acronyms():
    got = count_terms("A CTD cast and a Niskin rosette. PCR then qPCR. 16S rRNA, 16S again. Ctd is not it. random forest")
    assert got["CTD"] == 1
    assert got["PCR / qPCR"] == 2
    assert got["marker gene (16S, 18S, COI)"] == 2
    assert got["machine learning / embeddings"] == 1


def test_offline_run_writes_both_tables(tmp_path, capsys):
    pdfs = list((ROOT / "examples").glob("*/*.pdf"))
    if not pdfs:
        return
    src = tmp_path / "papers"
    src.mkdir()
    (src / "one.pdf").write_bytes(pdfs[0].read_bytes())
    assert main([str(src), "-o", str(tmp_path / "out"), "--offline"]) == 0
    assert (tmp_path / "out" / "papers.csv").exists() and (tmp_path / "out" / "topics.csv").exists()
    assert "PDF(s) read" in capsys.readouterr().out
