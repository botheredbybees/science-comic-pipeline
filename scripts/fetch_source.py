#!/usr/bin/env python3
"""Fetch an open-access paper from Europe PMC and split it into numbered text "pages" for claim checking.

    python scripts/fetch_source.py --doi 10.1038/s42003-021-02581-5 -o sources/pauli-2021
    python scripts/fetch_source.py --pmcid PMC8433442 -o sources/pauli-2021
    python scripts/fetch_source.py --xml saved.xml -o sources/pauli-2021        (no network)

Writes into the output folder:
  pages/p001.txt ...   one paragraph, figure/table caption, or table per file: the "pages" a claim's `page` refers to
  page-map.txt         one line per page: number, section, kind and the first words, to find a quote
  source.json          title, authors, year, DOI, PMCID and the licence statement with its URL
  <PMCID>.xml          the full text as fetched

The licence is printed first and written to source.json. Only CC BY, CC BY-SA and CC0 are usable as the
basis of an adaptation; for anything else the script exits with code 2 unless --force is given, and a
licence it cannot read is treated as unusable. Citation numbers (the superscripts) are dropped from the
text so that a quote does not end on a word with a digit stuck to it.

The "pages" are paragraphs, not printed pages: a claim cites `page: 7` meaning paragraph file p007.txt.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

API = "https://www.ebi.ac.uk/europepmc/webservices/rest"
USABLE = {"by", "by-sa", "cc0"}  # licence families that allow adaptation
SKIP_PARENTS = {"ref-list", "back", "table-wrap-foot", "fn-group"}


def get(url):
    """Fetch a URL with curl (Python's own HTTP client was refused by Europe PMC from some networks)."""
    if not shutil.which("curl"):
        raise RuntimeError("curl is needed to fetch from Europe PMC (or pass --xml with a saved file)")
    done = subprocess.run(["curl", "-sSfL", "--max-time", "60", url], capture_output=True, text=True)
    if done.returncode:
        raise RuntimeError(f"fetching {url} failed: {done.stderr.strip()}")
    return done.stdout


def pmcid_for_doi(doi):
    q = urllib.parse.quote(f'DOI:"{doi}"')
    data = json.loads(get(f"{API}/search?query={q}&format=json&resultType=core"))
    hits = data.get("resultList", {}).get("result", [])
    for h in hits:
        if h.get("pmcid"):
            return h["pmcid"]
    raise RuntimeError(f"no PMC full text for DOI {doi}: not open access in Europe PMC, or not indexed yet")


def licence_family(url, statement):
    """Return (family, label) from the licence URL, falling back to the wording of the statement."""
    text = f"{url} {statement}".lower()
    if "creativecommons.org/publicdomain/zero" in text or "cc0" in text:
        return "cc0", "CC0"
    m = re.search(r"creativecommons\.org/licenses/([a-z-]+)/([\d.]+)", text)
    if m:
        fam = m.group(1)
        return fam, f"CC {fam.upper()} {m.group(2)}"
    if "attribution-sharealike" in text:
        return "by-sa", "CC BY-SA"
    if "attribution" in text and "noncommercial" not in text and "noderiv" not in text:
        return "by", "CC BY"
    return "unknown", "unknown"


FLOATS = ("fig", "table-wrap")


def text_of(el, skip=()):
    """Text of an element, dropping bibliography citation numbers (and any `skip` tags, keeping
    the text that follows them), with whitespace collapsed."""
    out = []

    def walk(e):
        if (e.tag == "xref" and e.get("ref-type") == "bibr") or e.tag in skip:
            out.append(e.tail or "")
            return
        out.append(e.text or "")
        for c in e:
            walk(c)
            out.append("")
        out.append(e.tail or "")

    # walk children but not the tail of the root itself
    out.append(el.text or "")
    for c in el:
        walk(c)
    return re.sub(r"\s+", " ", "".join(out)).strip()


def strip_ns(root):
    for e in root.iter():
        if isinstance(e.tag, str) and "}" in e.tag:
            e.tag = e.tag.split("}", 1)[1]
    return root


def parse(xml_text):
    """Return (metadata, pages) where pages is a list of (section, kind, text)."""
    root = strip_ns(ET.fromstring(xml_text))
    art = root.find(".//article") if root.tag != "article" else root
    art = art if art is not None else root
    title = text_of(art.find(".//article-title")) if art.find(".//article-title") is not None else ""
    authors = []
    contribs = art.findall(".//contrib[@contrib-type='author']") or art.findall(".//contrib-group[@content-type='author']/contrib")
    for c in contribs:  # some publishers (MDPI) put the type on the group, not on each contrib
        n = c.find("name")
        if n is not None:
            authors.append(" ".join(filter(None, [text_of(n.find("given-names")) if n.find("given-names") is not None else "",
                                                  text_of(n.find("surname")) if n.find("surname") is not None else ""])))
    year = next((y.text for y in art.findall(".//pub-date/year") if y.text), "")
    doi = next((i.text for i in art.findall(".//article-id[@pub-id-type='doi']") if i.text), "")
    pmcid = next((i.text for i in art.findall(".//article-id[@pub-id-type='pmcid']") if i.text), "")
    lic = art.find(".//permissions/license")
    lic_url = ""
    if lic is not None:
        ref = next((e for e in lic.iter() if e.tag == "license_ref"), None)
        lic_url = (ref.text or "").strip() if ref is not None else (lic.get("href") or "")
    statement = text_of(lic) if lic is not None else ""
    if lic is not None and not lic_url:  # an ext-link inside the licence text, or the URL written in the statement
        lic_url = next((v for e in lic.iter() for k, v in e.attrib.items() if k.endswith("href") and "creativecommons.org" in v), "")
        m = re.search(r"https?://creativecommons\.org/[^\s)<>]+", statement)
        lic_url = lic_url or (m.group(0).rstrip(".,;") if m else "")
    family, label = licence_family(lic_url, statement)
    meta = {"title": title, "authors": authors, "year": year, "doi": doi, "pmcid": pmcid, "licence": label,
            "licence_family": family, "licence_url": lic_url, "licence_statement": statement,
            "licence_checked": f"Europe PMC full-text XML, {date.today().isoformat()}"}

    pages = []
    for p in art.findall(".//front//abstract//p"):
        pages.append(("Abstract", "abstract", text_of(p)))

    def float_pages(f, section):
        label = text_of(f.find("label")) if f.find("label") is not None else f.tag
        cap = f.find("caption")
        if cap is not None:
            pages.append((section, "caption", f"{label}. {text_of(cap)}"))
        if f.tag == "table-wrap":
            rows = [" | ".join(text_of(c) for c in r if c.tag in ("td", "th")) for r in f.iter("tr")]
            rows = [r for r in rows if r.strip(" |")]
            if rows:
                pages.append((section, "table", f"{label} rows: " + " ;; ".join(rows)))

    def visit(node, section, parents):
        for c in node:
            if c.tag in SKIP_PARENTS:
                continue
            if c.tag == "sec":
                t = c.find("title")
                visit(c, f"{section} / {text_of(t)}" if t is not None and section != "Body" else (text_of(t) if t is not None else section), parents)
            elif c.tag == "p":
                # Springer-style XML puts figures and tables inside the paragraph; keep the paragraph's own
                # text on its page and give each figure and table a page of its own.
                pages.append((section, "para", text_of(c, skip=FLOATS)))
                for f in c.iter():
                    if f.tag in FLOATS:
                        float_pages(f, section)
            elif c.tag in FLOATS:
                float_pages(c, section)
            else:
                visit(c, section, parents)

    body = art.find(".//body")
    if body is not None:
        visit(body, "Body", [])
    pages = [(s, k, t) for s, k, t in pages if t]
    return meta, pages


SLUG_SKIP = {"a", "an", "the", "of", "in", "on", "and", "for", "to", "with", "under", "from", "by", "at", "as", "is", "are", "how", "what", "can"}


def suggest_slug(meta):
    """first-author-surname, year and the first few significant words of the title, e.g. xia-2024-phytoplankton-diversity-spatial."""
    first = (meta["authors"][0].split()[-1] if meta["authors"] else "paper").lower()
    words = [w for w in re.findall(r"[a-z]+", meta["title"].lower()) if w not in SLUG_SKIP][:3]
    return "-".join([re.sub(r"[^a-z]", "", first), meta["year"] or "year"] + words)


def write(out, meta, pages, xml_text):
    out = Path(out)
    (out / "pages").mkdir(parents=True, exist_ok=True)
    lines = []
    count = {}
    for n, (section, kind, text) in enumerate(pages, 1):
        (out / "pages" / f"p{n:03d}.txt").write_text(text + "\n")
        # a locator such as "Discussion, paragraph 3" counts paragraphs within the section
        key = (section, kind)
        count[key] = count.get(key, 0) + 1
        what = f"{kind} {count[key]}" if kind in ("para", "abstract") else kind
        lines.append(f"p{n:03d} [{section}] {what}: {text[:70]}")
    (out / "page-map.txt").write_text("\n".join(lines) + "\n")
    (out / "source.json").write_text(json.dumps(meta, indent=2) + "\n")
    (out / f"{meta['pmcid'] or 'source'}.xml").write_text(xml_text)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--doi")
    src.add_argument("--pmcid")
    src.add_argument("--xml", help="a full-text XML file already saved from Europe PMC")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--force", action="store_true", help="write the pages even if the licence does not allow adaptation")
    args = ap.parse_args(argv)

    if args.xml:
        xml_text = Path(args.xml).read_text()
    else:
        pmcid = args.pmcid or pmcid_for_doi(args.doi)
        xml_text = get(f"{API}/{pmcid}/fullTextXML")
    meta, pages = parse(xml_text)
    usable = meta["licence_family"] in USABLE
    print(f"Licence: {meta['licence']} {meta['licence_url']}".rstrip())
    print(f"Title:   {meta['title']}")
    print(f"Suggested slug: {suggest_slug(meta)}")
    if meta["licence_statement"]:
        cut = meta["licence_statement"][:300]
        print("Statement: " + (cut if len(meta["licence_statement"]) <= 300 else cut.rsplit(" ", 1)[0] + " ..."))
    if not usable and not args.force:
        print("Not usable as the basis of an adaptation (needs CC BY, CC BY-SA or CC0). Nothing written; use --force to override.")
        return 2
    if not usable:
        print("WARNING: licence does not allow adaptation; written because of --force. Do not publish the result.")
    if meta["licence_family"] == "by-sa":
        print("ShareAlike: the comic must be released under the same licence (CC BY-SA).")
    write(args.out, meta, pages, xml_text)
    print(f"Wrote {len(pages)} pages to {args.out}/pages; map in {args.out}/page-map.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
