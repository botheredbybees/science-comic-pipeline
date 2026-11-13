import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_source as F  # noqa: E402

XML = """<?xml version="1.0"?>
<article xmlns:ali="http://www.niso.org/schemas/ali/1.0/">
 <front><article-meta>
  <article-id pub-id-type="pmcid">PMC1</article-id><article-id pub-id-type="doi">10.1/x</article-id>
  <title-group><article-title>Plankton and <italic>carbon</italic></article-title></title-group>
  <contrib-group><contrib contrib-type="author"><name><surname>Lin</surname><given-names>Yajuan</given-names></name></contrib></contrib-group>
  <pub-date pub-type="epub"><year>2017</year></pub-date>
  <permissions><license><ali:license_ref>https://creativecommons.org/licenses/%s/4.0/</ali:license_ref>
   <license-p>Licensed under a Creative Commons licence.</license-p></license></permissions>
  <abstract><p>We found that diatoms matter.</p></abstract>
 </article-meta></front>
 <body>
  <sec><title>Introduction</title>
   <p>Density of plankton<xref ref-type="bibr" rid="b1">1</xref> is high<xref ref-type="bibr" rid="b2">2,3</xref>.</p>
   <sec><title>Methods</title><p>We sampled water.</p></sec>
  </sec>
  <fig id="f1"><label>Figure 1</label><caption><p>A map.</p></caption></fig>
 </body>
 <back><ref-list><ref><p>Should not appear</p></ref></ref-list></back>
</article>"""


def test_parse_pages_and_metadata():
    meta, pages = F.parse(XML % "by")
    assert meta["title"] == "Plankton and carbon"
    assert meta["authors"] == ["Yajuan Lin"] and meta["year"] == "2017" and meta["doi"] == "10.1/x"
    assert meta["licence_family"] == "by" and meta["licence"] == "CC BY 4.0"
    texts = [t for _, _, t in pages]
    assert texts[0] == "We found that diatoms matter."
    assert "Density of plankton is high." in texts[1]  # citation numbers dropped
    assert "We sampled water." in texts and "Figure 1. A map." in texts
    assert not any("Should not appear" in t for t in texts)
    assert [s for s, _, _ in pages][1:3] == ["Introduction", "Introduction / Methods"]


def test_licence_families():
    assert F.licence_family("https://creativecommons.org/licenses/by-sa/4.0/", "")[0] == "by-sa"
    assert F.licence_family("https://creativecommons.org/licenses/by-nc-nd/4.0/", "")[0] == "by-nc-nd"
    assert F.licence_family("", "no licence here")[0] == "unknown"


def test_writes_pages_and_refuses_a_noderivs_licence(tmp_path, capsys):
    ok, bad = tmp_path / "ok.xml", tmp_path / "bad.xml"
    ok.write_text(XML % "by")
    bad.write_text(XML % "by-nc-nd")
    assert F.main(["--xml", str(ok), "-o", str(tmp_path / "out")]) == 0
    assert (tmp_path / "out" / "pages" / "p001.txt").read_text().strip() == "We found that diatoms matter."
    assert json.loads((tmp_path / "out" / "source.json").read_text())["licence"] == "CC BY 4.0"
    assert F.main(["--xml", str(bad), "-o", str(tmp_path / "out2")]) == 2
    assert not (tmp_path / "out2").exists()


def test_figures_and_tables_inside_a_paragraph_get_their_own_pages(tmp_path):
    xml = (XML % "by").replace(
        "<sec><title>Methods</title>",
        '<sec><title>Methods</title><p>Krill ate diatoms (Table 1) and grew.'
        '<table-wrap id="t1"><label>Table 1</label><caption><p>Diets.</p></caption>'
        '<table><tr><th>Taxon</th><th>Share</th></tr><tr><td>Diatoms</td><td>41%</td></tr></table></table-wrap>'
        '<fig id="f2"><label>Figure 2</label><caption><p>A net.</p></caption></fig> Then they stopped.</p>')
    meta, pages = F.parse(xml)
    texts = [t for _, _, t in pages]
    assert "Krill ate diatoms (Table 1) and grew. Then they stopped." in texts  # the paragraph, without the floats
    assert "Table 1. Diets." in texts and "Figure 2. A net." in texts
    assert any(t.startswith("Table 1 rows:") and "Diatoms | 41%" in t for t in texts)
    F.write(tmp_path, meta, pages, xml)
    pm = (tmp_path / "page-map.txt").read_text()
    assert "[Introduction] para 1:" in pm and "[Introduction / Methods] para 1:" in pm and "caption:" in pm
