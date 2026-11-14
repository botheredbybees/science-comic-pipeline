#!/usr/bin/env python3
"""A local catalogue of the papers and comics: what exists, what is stale, what is waiting for a decision.

    python scripts/catalogue.py                      # rebuild private/catalogue.db and print a summary
    python scripts/catalogue.py --stale              # comics whose PDF is older than their storyboard or the renderer
    python scripts/catalogue.py --uses ctd           # comics that use an asset (a prop, body, held object, outfit or hair)
    python scripts/catalogue.py --pending-jokes      # jokes still waiting for a person (approve them with scripts/jokes.py)
    python scripts/catalogue.py --variety            # each comic's McCloud mix: scene-to-scene, moments, glosses
    python scripts/catalogue.py --todo-papers 30     # open-licence papers from the triage that are not comics yet
    python scripts/catalogue.py --editions           # when each comic was last made, and against which renderer
    python scripts/catalogue.py --sql "select slug, panels from comics order by panels desc"

The database is an index, not the source of truth: the comics' files and the triage tables (`scripts/triage_papers.py`) are,
and every run rebuilds the tables from them. The one exception is `editions`, a history that is only ever added to: each time a
comic's PDF has changed since the last run, a row records the date, the renderer's version and the checks. It lives in
`private/` (not committed), because it names private papers.

Tables: papers, topics, comics, comic_assets, jokes, editions.
"""
import argparse
import csv
import hashlib
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_storyboard import _figure_only, validate, variety  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

DERIVED = """
DROP TABLE IF EXISTS papers;
DROP TABLE IF EXISTS topics;
DROP TABLE IF EXISTS comics;
DROP TABLE IF EXISTS comic_assets;
DROP TABLE IF EXISTS jokes;
CREATE TABLE papers (triage_set TEXT, file TEXT, doi TEXT, doi_source TEXT, title TEXT, year TEXT, licence TEXT, class TEXT, oa_status TEXT, pages TEXT);
CREATE TABLE topics (triage_set TEXT, category TEXT, term TEXT, papers INTEGER, mentions INTEGER);
CREATE TABLE comics (slug TEXT PRIMARY KEY, location TEXT, private INTEGER, title TEXT, paper_title TEXT, doi TEXT, year INTEGER, licence TEXT,
                     beats INTEGER, panels INTEGER, claims INTEGER, jokes INTEGER, jokes_pending INTEGER, errors INTEGER, warnings INTEGER,
                     figures_only_pct INTEGER, pdf TEXT, pdf_time TEXT, storyboard_time TEXT, stale INTEGER, stale_reason TEXT,
                     scene_pct INTEGER, moment_pct INTEGER, no_word_picture_pct INTEGER, devices TEXT);
CREATE TABLE comic_assets (slug TEXT, kind TEXT, name TEXT, uses INTEGER);
CREATE TABLE jokes (slug TEXT, panel TEXT, note TEXT, confirmed INTEGER);
"""
KEEP = "CREATE TABLE IF NOT EXISTS editions (slug TEXT, made TEXT, renderer TEXT, git_head TEXT, storyboard_sha TEXT, pages INTEGER, errors INTEGER, warnings INTEGER);"


def stamp(t):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(t))


def renderer_files(root):
    return sorted((root / "renderers" / "xkcd").glob("*.py")) + [root / "schema" / "storyboard.schema.json"]


def renderer_version(root):
    """A short hash of the renderer and schema sources: what a PDF was (or would now be) drawn with."""
    h = hashlib.sha1()
    for f in renderer_files(root):
        h.update(f.read_bytes())
    return h.hexdigest()[:10]


def git_head(root):
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def pdf_pages(pdf):
    try:
        out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return 0
    for line in out.splitlines():
        if line.startswith("Pages:"):
            return int(line.split()[1])
    return 0


def walk_props(staging):
    for pr in (staging or {}).get("props", []):
        yield pr
        yield from walk_props(pr.get("staging"))


def find_comics(root):
    for loc in ("examples", "private"):
        base = root / loc
        if base.is_dir():
            for sub in sorted(base.iterdir()):
                if (sub / "storyboard.yaml").is_file():
                    yield loc, sub


def load_triage(db, root):
    for d in sorted((root / "private" / "triage").glob("*/")):
        pf, tf = d / "papers.csv", d / "topics.csv"
        if pf.exists():
            with open(pf, newline="") as f:
                for r in csv.DictReader(f):
                    db.execute("INSERT INTO papers VALUES (?,?,?,?,?,?,?,?,?,?)", (d.name, r.get("file"), (r.get("doi") or "").lower(), r.get("doi_source", ""),
                               r.get("title"), r.get("year"), r.get("licence"), r.get("class"), r.get("oa_status"), r.get("pages")))
        if tf.exists():
            with open(tf, newline="") as f:
                for r in csv.DictReader(f):
                    db.execute("INSERT INTO topics VALUES (?,?,?,?,?)", (d.name, r["category"], r["term"], int(r["papers"]), int(r["mentions"])))


def load_comic(db, root, loc, folder, rversion, newest_renderer):
    slug = folder.name
    sb = folder / "storyboard.yaml"
    doc = yaml.safe_load(sb.read_text())
    meta = doc.get("meta", {})
    src = meta.get("source") or (meta.get("sources") or [{}])[0]  # a topic comic is catalogued under its first source
    errors, warnings = validate(doc)
    panels = [p for b in doc["beats"] for p in b["panels"]]
    cast_bodies = {c["id"]: (c.get("appearance") or {}).get("body", "stick") for c in doc["cast"]}
    jokes = [(p["id"], p["humour"]) for p in panels if "humour" in p]
    pending = sum(1 for _, h in jokes if not h.get("keeps_claims_intact"))
    bare = sum(1 for p in panels if _figure_only(p, cast_bodies))
    pdfs = sorted(folder.glob("*.pdf"), key=lambda f: f.stat().st_mtime)
    pdf = (folder / f"{slug}.pdf") if (folder / f"{slug}.pdf").exists() else (pdfs[-1] if pdfs else None)
    sb_time = sb.stat().st_mtime
    stale, reason = 0, ""
    if pdf is None:
        stale, reason = 1, "no PDF"
    elif pdf.stat().st_mtime < sb_time:
        stale, reason = 1, "storyboard changed after the PDF"
    elif pdf.stat().st_mtime < newest_renderer:
        stale, reason = 1, "renderer or schema changed after the PDF"
    vstats, _ = variety(doc)
    devs = ", ".join(f"{k} {v}" for k, v in sorted(vstats["devices"].items()))
    db.execute("INSERT INTO comics VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
               (slug, loc, int(loc == "private" or bool(meta.get("private"))), meta.get("title"), src.get("title"), (src.get("doi") or "").lower(), src.get("year"),
                src.get("licence"), len(doc["beats"]), len(panels), len(doc["claims"]), len(jokes), pending, len(errors), len(warnings),
                round(100 * bare / max(len(panels), 1)), str(pdf.relative_to(root)) if pdf else "", stamp(pdf.stat().st_mtime) if pdf else "", stamp(sb_time), stale, reason,
                vstats["scene_pct"], vstats["moment_pct"], vstats["no_word_picture_pct"], devs))
    use = {}

    def add(kind, name):
        if name:
            use[(kind, str(name))] = use.get((kind, str(name)), 0) + 1

    for c in doc["cast"]:
        app = c.get("appearance") or {}
        add("hair", app.get("hair"))
        add("outfit", app.get("outfit") or ("labcoat" if app.get("coat") else None))
        if app.get("glasses"):
            add("look", "glasses")
    for p in panels:
        st = p.get("staging") or {}
        for pr in walk_props(st):
            add("prop", pr["kind"])
        for ch in st.get("characters", []):
            add("body", ch.get("body") or cast_bodies.get(ch["id"], "stick"))
            add("holding", ch.get("holding"))
    for (kind, name), n in sorted(use.items()):
        db.execute("INSERT INTO comic_assets VALUES (?,?,?,?)", (slug, kind, name, n))
    for pid, h in jokes:
        db.execute("INSERT INTO jokes VALUES (?,?,?,?)", (slug, pid, (h.get("note") or "")[:160], int(bool(h.get("keeps_claims_intact")))))
    if pdf is not None:  # an edition is recorded once for each distinct PDF
        made = stamp(pdf.stat().st_mtime)
        if not db.execute("SELECT 1 FROM editions WHERE slug=? AND made=?", (slug, made)).fetchone():
            sha = hashlib.sha1(sb.read_bytes()).hexdigest()[:10]
            db.execute("INSERT INTO editions VALUES (?,?,?,?,?,?,?,?)", (slug, made, rversion, git_head(root), sha, pdf_pages(pdf), len(errors), len(warnings)))


def build(root=ROOT, db_path=None):
    """Rebuild the derived tables (keeping the edition history) and return the open connection."""
    root = Path(root)
    db_path = Path(db_path) if db_path else root / "private" / "catalogue.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(db_path)
    db.executescript(DERIVED + KEEP)
    rver = renderer_version(root)
    newest = max(f.stat().st_mtime for f in renderer_files(root) if f.exists())
    load_triage(db, root)
    for loc, folder in find_comics(root):
        load_comic(db, root, loc, folder, rver, newest)
    db.commit()
    return db


def show(rows, headers):
    rows = [tuple("" if v is None else str(v) for v in r) for r in rows]
    if not rows:
        print("(nothing)")
        return
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    widths = [min(w, 70) for w in widths]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)))
    for r in rows:
        print("  ".join(v[:w].ljust(w) for v, w in zip(r, widths)))


def summary(db):
    def n(q):
        return db.execute(q).fetchone()[0]

    total = n("select count(*) from comics")
    public = n("select count(*) from comics where location = 'examples'")
    stale = n("select count(*) from comics where stale = 1")
    pending = n("select coalesce(sum(jokes_pending), 0) from comics")
    print(f"{total} comic(s) ({public} public examples), {stale} with a stale PDF, {pending} joke(s) awaiting a person")
    classes = db.execute("select class, count(distinct coalesce(nullif(doi,''), file)) from papers group by class order by 2 desc").fetchall()
    if classes:
        print("papers triaged: " + ", ".join(f"{c} {k}" for k, c in classes))
    show(db.execute("select slug, location, panels, claims, warnings, jokes_pending, figures_only_pct, stale from comics order by location desc, slug").fetchall(),
         ["comic", "where", "panels", "claims", "warn", "jokes?", "bare%", "stale"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=str(ROOT), help="the repo to catalogue (default: this one)")
    ap.add_argument("--db", help="database file (default: <root>/private/catalogue.db)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--stale", action="store_true")
    g.add_argument("--uses", metavar="ASSET")
    g.add_argument("--pending-jokes", action="store_true")
    g.add_argument("--variety", action="store_true")
    g.add_argument("--todo-papers", nargs="?", const=25, type=int, metavar="N")
    g.add_argument("--editions", action="store_true")
    g.add_argument("--sql", metavar="QUERY")
    args = ap.parse_args(argv)
    db = build(args.root, args.db)
    if args.stale:
        show(db.execute("select slug, location, pdf_time, stale_reason from comics where stale=1 order by slug").fetchall(), ["comic", "where", "PDF made", "why"])
    elif args.uses:
        show(db.execute("select c.slug, a.kind, a.name, a.uses from comic_assets a join comics c using(slug) where a.name=? order by a.uses desc", (args.uses,)).fetchall(),
             ["comic", "kind", "asset", "uses"])
    elif args.variety:
        show(db.execute("select slug, panels, scene_pct, moment_pct, no_word_picture_pct, devices from comics order by scene_pct desc").fetchall(),
             ["comic", "panels", "scene-to-scene%", "moments%", "no word-picture%", "devices"])
    elif args.pending_jokes:
        show(db.execute("select slug, panel, note from jokes where confirmed=0 order by slug, panel").fetchall(), ["comic", "panel", "note"])
    elif args.todo_papers is not None:
        show(db.execute("""select p.year, p.doi, p.title from papers p where p.class='usable' and p.doi<>''
                           and p.doi not in (select doi from comics where doi<>'') group by p.doi order by p.year desc limit ?""", (args.todo_papers,)).fetchall(),
             ["year", "doi", "title"])
    elif args.editions:
        show(db.execute("select slug, made, renderer, git_head, pages, warnings from editions order by slug, made").fetchall(), ["comic", "made", "renderer", "git", "pages", "warn"])
    elif args.sql:
        cur = db.execute(args.sql)
        show(cur.fetchall(), [d[0] for d in cur.description])
    else:
        summary(db)
    return 0


if __name__ == "__main__":
    sys.exit(main())
