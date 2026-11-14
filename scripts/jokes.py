#!/usr/bin/env python3
"""List, read and approve the jokes in the comics. A joke is a panel with a `humour` block; it waits for a person until
`keeps_claims_intact` is true.

    python scripts/jokes.py list                       # every joke still waiting, with the line that carries it
    python scripts/jokes.py list --comic nester        # only comics whose name contains this
    python scripts/jokes.py show nester B6.13          # one joke in full: scene, caption, lines, the claims it sits on
    python scripts/jokes.py approve nester B6.13 B7.2  # approve one or more
    python scripts/jokes.py approve nester --all       # approve every joke in a comic
    python scripts/jokes.py revoke nester B6.13        # take an approval back
    python scripts/jokes.py edit nester B6.13 --line 2 --text "New wording."   # reword a line (or --note "..." for the note)
    python scripts/jokes.py cut nester B6.13 --line 2  # reject: delete the numbered speech line(s) and the joke flag
    python scripts/jokes.py review                     # step through the waiting jokes: Enter accepts; edit / reject / skip / quit

A comic is found by a unique part of its name. Approving changes only the one `keeps_claims_intact` flag, in place, in the
comic's `beats/*.yaml` (or `storyboard.yaml` when there are no beat files) and then rebuilds `storyboard.yaml`; nothing else in
the file is reformatted. `edit` also changes only the one line's text where it can; text with a colon, a quote or a `#` in it, and `cut`,
rewrite the file with PyYAML, so that file may be re-flowed.

What to judge (the five questions of skills/humour-pass): is every number, unit and hedge exactly as in the claim; is it plainly
the comic's own voice; is the butt an organism, an instrument or the comic itself and not the authors or any people; does it leave
every caveat at full strength; would it read as honest to the authors.
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_storyboard import main as build_storyboard  # noqa: E402
from catalogue import find_comics  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ("1 numbers, units, hedges as in the claim   2 plainly the comic's voice   3 the butt is not the authors or people\n"
             "4 every caveat stays at full strength   5 honest to the authors")


def comics(root):
    return {folder.name: (loc, folder) for loc, folder in find_comics(root)}


def pick(root, part):
    found = [(n, v) for n, v in comics(root).items() if part.lower() in n.lower()]
    if len(found) != 1:
        names = ", ".join(n for n, _ in found) or "none"
        raise SystemExit(f"'{part}' must match exactly one comic (matches: {names})")
    return found[0][0], found[0][1][1]


def sources(folder):
    """The files that hold the panels: beat files if there are any, else the storyboard."""
    beats = sorted((folder / "beats").glob("B*.yaml"))
    return beats if beats else [folder / "storyboard.yaml"]


def load_jokes(folder):
    """Every joke in the comic, from the built storyboard: a list of dicts with the panel and what it says."""
    doc = yaml.safe_load((folder / "storyboard.yaml").read_text())
    claims = {c["id"]: c for c in doc["claims"]}
    out = []
    for beat in doc["beats"]:
        for p in beat["panels"]:
            if "humour" not in p:
                continue
            lines = p.get("speech", [])
            out.append({"panel": p["id"], "beat": beat.get("title", beat["id"]), "scene": p.get("scene", ""), "lines": lines,
                        "humour": p["humour"], "confirmed": bool(p["humour"].get("keeps_claims_intact")),
                        "claims": [claims[c] for c in p.get("claim_ids", []) if c in claims]})
    return out


def joke_text(j):
    """The line or lines that carry the joke: what the characters say, or the note if the gag is a picture."""
    said = [f'{l["speaker"]}: {l["text"]}' for l in j["lines"] if l.get("kind", "say") != "caption"]
    return " / ".join(said) if said else "(a picture gag) " + j["humour"].get("note", "")[:80]


def edit_flag(text, panel, value):
    """Set `keeps_claims_intact` for one panel, in place. Returns the new text, or None if the panel is not in this text."""
    m = re.search(rf"(?m)^[ \t]*(?:- )?id: {re.escape(panel)}(?![\w.])", text)
    if not m:
        return None
    nxt = re.search(r"(?m)^[ \t]*- id: ", text[m.end():])
    end = m.end() + nxt.start() if nxt else len(text)
    block = text[m.start():end]
    new, n = re.subn(r"keeps_claims_intact: *(true|false)", f"keeps_claims_intact: {'true' if value else 'false'}", block, count=1)
    return text[:m.start()] + new + text[end:] if n else None


def set_confirmed(folder, panel, value):
    for f in sources(folder):
        new = edit_flag(f.read_text(), panel, value)
        if new is not None:
            f.write_text(new)
            return True
    return False


def rebuild(folder):
    if (folder / "head.yaml").exists():
        build_storyboard([str(folder)])


def cut_joke(folder, panel, lines):
    """Delete a joke: its `humour` block and the given speech lines (1-based, as `show` numbers them)."""
    for f in sources(folder):
        data = yaml.safe_load(f.read_text())
        beats = data if isinstance(data, list) else data.get("beats", [])
        for beat in beats:
            for p in beat["panels"]:
                if p["id"] == panel:
                    p.pop("humour", None)
                    drop = {n - 1 for n in lines}
                    p["speech"] = [l for i, l in enumerate(p.get("speech", [])) if i not in drop]
                    f.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=200))
                    return True
    return False


PLAIN_OK = re.compile(r"[^:#\"'\\{}\[\]&*!|>%@`,\n][^:#\"'\\\n]*")


def panel_block(text, panel):
    """(start, end) of one panel's block in a beat or storyboard file, or None."""
    m = re.search(rf"(?m)^[ \t]*(?:- )?id: {re.escape(panel)}(?![\w.])", text)
    if not m:
        return None
    nxt = re.search(r"(?m)^[ \t]*- id: ", text[m.end():])
    return m.start(), m.end() + nxt.start() if nxt else len(text)


def replace_in_block(text, panel, old, new):
    """Replace one exact piece of text inside a panel's block, in place, if it appears once and `new` is safe to drop into a YAML
    scalar as it is (no colon, quote, backslash or `#`). Returns the new text, or None if that is not possible."""
    span = panel_block(text, panel)
    if not span or not PLAIN_OK.fullmatch(new) or "\n" in new:
        return None
    a, b = span
    block = text[a:b]
    if block.count(old) != 1:
        return None
    return text[:a] + block.replace(old, new) + text[b:]


def edit_text(folder, panel, new, line=None, note=False):
    """Reword a speech line (1-based `line`) or the humour note of a panel. Returns True if done."""
    for f in sources(folder):
        text = f.read_text()
        data = yaml.safe_load(text)
        beats = data if isinstance(data, list) else data.get("beats", [])
        for beat in beats:
            for p in beat["panels"]:
                if p["id"] != panel:
                    continue
                if note:
                    old = (p.get("humour") or {}).get("note")
                    if old is None:
                        return False
                else:
                    if not line or line > len(p.get("speech", [])):
                        return False
                    old = p["speech"][line - 1]["text"]
                fast = replace_in_block(text, panel, old, new)
                if fast is not None:
                    f.write_text(fast)
                    return True
                if note:
                    p["humour"]["note"] = new
                else:
                    p["speech"][line - 1]["text"] = new
                f.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=200))
                return True
    return False


def last_character_line(j):
    """The 1-based number of the last non-caption speech line: usually the joke itself."""
    nums = [i for i, l in enumerate(j["lines"], 1) if l.get("kind", "say") != "caption"]
    return nums[-1] if nums else None


def show(name, j, page=None):
    print(f"{name}  {j['panel']}" + (f"  (PDF page {page})" if page else "") + f"   [{'approved' if j['confirmed'] else 'waiting'}]")
    print(f"  scene:   {j['scene']}")
    for i, l in enumerate(j["lines"], 1):
        kind = "CAPTION" if l.get("kind", "say") == "caption" else l["speaker"]
        print(f"  [{i}] {kind}: {l['text']}")
    print(f"  note:    {j['humour'].get('note', '')}")
    for c in j["claims"]:
        print(f"  claim {c['id']} ({c['status']}): {c['text']}")
    print("  judge:   " + QUESTIONS.replace("\n", "\n           "))


def page_of(folder, panel):
    """Which PDF page a panel is on (by rendering the storyboard), or None."""
    try:
        sys.path.insert(0, str(ROOT / "renderers" / "xkcd"))
        import render
        svgs, _ = render.render_pages(yaml.safe_load((folder / "storyboard.yaml").read_text()))
        for n, svg in enumerate(svgs, 1):
            if f'id="panel-{panel}"' in svg:
                return n
    except Exception:  # a page number is a convenience, never a reason to stop
        return None
    return None


def waiting(root, part=None):
    for name, (loc, folder) in sorted(comics(root).items()):
        if part and part.lower() not in name.lower():
            continue
        for j in load_jokes(folder):
            if not j["confirmed"]:
                yield name, folder, j


def cmd_list(root, part):
    rows = list(waiting(root, part))
    if not rows:
        print("no jokes waiting")
        return 0
    for name, _, j in rows:
        print(f"{name[:32]:32} {j['panel']:7} {joke_text(j)[:110]}")
    print(f"\n{len(rows)} joke(s) waiting. Read one with `show <comic> <panel>`, approve with `approve <comic> <panel>`, or `review`.")
    return 0


def cmd_review(root, part, ask=input):
    """Step through the waiting jokes. Enter accepts; `e` rewords a line and shows the joke again; `r` rejects (deletes the joke's
    line, or keeps the lines and drops only the joke flag); `s` skips; `q` quits."""
    rows = list(waiting(root, part))
    if not rows:
        print("no jokes waiting")
        return 0
    done = {"accepted": 0, "edited": 0, "rejected": 0, "skipped": 0}
    for i, (name, folder, j) in enumerate(rows, 1):
        print(f"\n--- {i} of {len(rows)} " + "-" * 50)
        edited = False
        while True:
            fresh = next((x for x in load_jokes(folder) if x["panel"] == j["panel"]), j)
            show(name, fresh, page_of(folder, j["panel"]) if ask is input else None)
            a = ask("\n[A]ccept (Enter)  [e]dit  [r]eject  [s]kip  [q]uit > ").strip().lower()
            if a in ("", "a", "accept", "y", "yes"):
                set_confirmed(folder, j["panel"], True)
                rebuild(folder)
                done["edited" if edited else "accepted"] += 1
                break
            if a in ("e", "edit"):
                default = last_character_line(fresh)
                n = ask(f"which line to reword (number; Enter = {default})? ").strip()
                n = int(n) if n.isdigit() else default
                if not n or n > len(fresh["lines"]):
                    print("no such line")
                    continue
                print("now: " + fresh["lines"][n - 1]["text"])
                new = ask("new text (Enter keeps it)? ").strip()
                if new and edit_text(folder, j["panel"], new, line=n):
                    rebuild(folder)
                    edited = True
                continue  # show the joke again, and ask again with Enter = accept
            if a in ("r", "reject", "c", "cut", "n", "no"):
                default = last_character_line(fresh)
                ans = ask(f"delete which line(s) (numbers, e.g. 2 or 2,3; Enter = {default}; 'keep' = keep the lines, drop only the joke flag)? ").strip().lower()
                nums = [] if ans == "keep" else [int(x) for x in ans.replace(",", " ").split() if x.isdigit()] or ([default] if default else [])
                if cut_joke(folder, j["panel"], nums):
                    rebuild(folder)
                    done["rejected"] += 1
                break
            if a in ("s", "skip"):
                done["skipped"] += 1
                break
            if a in ("q", "quit"):
                print(f"\nstopped: {done['accepted']} accepted, {done['edited']} edited and accepted, {done['rejected']} rejected, {done['skipped']} skipped")
                return 0
    print(f"\ndone: {done['accepted']} accepted, {done['edited']} edited and accepted, {done['rejected']} rejected, {done['skipped']} skipped")
    return 0


def main(argv=None, root=ROOT, ask=input):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=str(root))
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("--comic")
    p = sub.add_parser("show"); p.add_argument("comic"); p.add_argument("panel")
    for name in ("approve", "revoke"):
        p = sub.add_parser(name); p.add_argument("comic"); p.add_argument("panels", nargs="*"); p.add_argument("--all", action="store_true")
    p = sub.add_parser("cut"); p.add_argument("comic"); p.add_argument("panel"); p.add_argument("--line", type=int, action="append", default=[])
    p = sub.add_parser("edit"); p.add_argument("comic"); p.add_argument("panel"); p.add_argument("--text", required=True)
    p.add_argument("--line", type=int); p.add_argument("--note", action="store_true", help="reword the humour note instead of a speech line")
    p = sub.add_parser("review"); p.add_argument("--comic")
    args = ap.parse_args(argv)
    root = Path(args.root)
    if args.cmd == "list":
        return cmd_list(root, args.comic)
    if args.cmd == "review":
        return cmd_review(root, args.comic, ask)
    name, folder = pick(root, args.comic)
    jokes = {j["panel"]: j for j in load_jokes(folder)}
    if args.cmd == "show":
        if args.panel not in jokes:
            raise SystemExit(f"{name} has no joke on panel {args.panel} (jokes: {', '.join(jokes) or 'none'})")
        show(name, jokes[args.panel], page_of(folder, args.panel))
        return 0
    if args.cmd in ("approve", "revoke"):
        value = args.cmd == "approve"
        panels = [pn for pn, j in jokes.items() if j["confirmed"] != value] if args.all else args.panels
        if not panels:
            print("nothing to do")
            return 0
        for pn in panels:
            if pn not in jokes:
                raise SystemExit(f"{name} has no joke on panel {pn}")
            print(f"{name} {pn}: {'approved' if value else 'approval removed'}" if set_confirmed(folder, pn, value) else f"{name} {pn}: not found in the beat files")
        rebuild(folder)
        return 0
    if args.cmd == "edit":
        if args.panel not in jokes:
            raise SystemExit(f"{name} has no joke on panel {args.panel}")
        if not args.note and not args.line:
            raise SystemExit("say which speech line with --line N (as `show` numbers them), or use --note")
        ok = edit_text(folder, args.panel, args.text, line=args.line, note=args.note)
        print(f"{name} {args.panel}: {'reworded' if ok else 'not found'}")
        rebuild(folder)
        return 0
    if args.cmd == "cut":
        if args.panel not in jokes:
            raise SystemExit(f"{name} has no joke on panel {args.panel}")
        print(f"{name} {args.panel}: joke cut" if cut_joke(folder, args.panel, args.line) else "not found")
        rebuild(folder)
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
