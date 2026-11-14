#!/usr/bin/env python3
"""Pick cards from one or more papers and write them as a claims ledger a storyboard can use.

    python scripts/cards_to_claims.py \\
        --from smith-2020=cards/smith/cards.yaml:3,7,11-14 \\
        --from jones-2019=cards/jones/cards.yaml:all \\
        -o private/<slug>/claims.yaml --show

`extract_cards.py` writes one `cards.yaml` per paper, and every card is numbered C1, C2, ... from 1 within its paper. A comic that
draws on several papers needs one ledger, so this script:

  * takes the cards you choose (`all`, or card numbers and ranges: `3,7,11-14`; the `C` prefix is optional),
  * renumbers them C1, C2, ... across the whole ledger and sets `source.ref` to the name before the `=` (the paper's id in
    `meta.sources`),
  * maps the extractor's `future_research` kind to `argument` (the schema has no such kind) and says so in the note,
  * carries the second model's verdict into the note, and leaves every claim `unverified`,
  * writes `claims-map.yaml` beside the ledger (new id -> paper and original card), so a claim can be traced back.

A claim is marked `verified` only after a person has read its paraphrase against its quote. Use `--show` to print every chosen
card as claim and quote side by side, edit the wording in the ledger where the claim says more than the quote, then run
`--reviewed-by "Your name"` (with `--append`, or on the same cards) or set `status: verified` yourself. `--reviewed-by` records who
read them; it is not a substitute for reading them.

`--append` adds to an existing ledger and continues its numbering. `--pages-root DIR` also copies each paper's `pages/` folder to
`DIR/<ref>/pages`, which is where `check_quotes.py --pages-root` looks.
"""
import argparse
import shutil
import sys
from pathlib import Path

import yaml

KIND_MAP = {"future_research": "argument"}


def parse_spec(spec, n_cards):
    """Card numbers from 'all' or '3,7,11-14' (a leading C is allowed); returns a sorted-as-given list of ints."""
    spec = (spec or "all").strip()
    if spec.lower() == "all":
        return list(range(1, n_cards + 1))
    out = []
    for part in spec.replace("C", "").replace("c", "").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def load_cards(path):
    p = Path(path)
    f = p / "cards.yaml" if p.is_dir() else p
    doc = yaml.safe_load(f.read_text())
    cards = doc["claims"] if isinstance(doc, dict) else doc
    return {int(str(c["id"]).lstrip("Cc")): c for c in cards}, f.parent


def convert(selections, start=1, reviewed_by=""):
    """selections: [(ref, {number: card}, [numbers])]. Returns (claims, map) numbered from `start`."""
    claims, cmap, n = [], {}, start
    for ref, by_num, numbers in selections:
        for num in numbers:
            if num not in by_num:
                raise KeyError(f"{ref} has no card C{num}")
            c = by_num[num]
            src = dict(c["source"])
            src["ref"] = ref
            kind = KIND_MAP.get(c["kind"], c["kind"])
            note = f"model-extracted card {ref} C{num}"
            if kind != c["kind"]:
                note += f"; the authors call for further research (kind mapped from {c['kind']})"
            mc = c.get("model_check")
            if mc:
                note += f"; second-model check: {mc.get('verdict', '?')}" + (f" ({mc['why']})" if mc.get("why") else "")
            status = "unverified"
            if reviewed_by:
                status = "verified"
                note += f"; paraphrase read against its quote by {reviewed_by}"
            cid = f"C{n}"
            claims.append({"id": cid, "text": c["text"], "kind": kind, "source": src, "status": status, "note": note})
            cmap[cid] = {"ref": ref, "card": f"C{num}"}
            n += 1
    return claims, cmap


def show(claims):
    for c in claims:
        print(f"{c['id']} [{c['kind']}] {c['text']}\n    QUOTE (page {c['source']['page']}, {c['source']['ref']}): {c['source']['quote']}\n    {c['note']}\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="sources", action="append", required=True, metavar="REF=PATH[:SPEC]",
                    help="a paper's id, its cards.yaml (or the folder holding it), and optionally which cards (default all)")
    ap.add_argument("-o", "--out", required=True, help="the claims ledger to write")
    ap.add_argument("--append", action="store_true", help="add to an existing ledger and continue its numbering")
    ap.add_argument("--show", action="store_true", help="print each chosen card as claim and quote, for reading")
    ap.add_argument("--reviewed-by", default="", help="mark the chosen claims verified and record who read them against their quotes")
    ap.add_argument("--pages-root", default="", help="also copy each paper's pages/ folder to DIR/<ref>/pages")
    args = ap.parse_args(argv)

    selections, folders = [], {}
    for item in args.sources:
        ref, _, rest = item.partition("=")
        path, _, spec = rest.rpartition(":") if ":" in rest and not Path(rest).exists() else (rest, "", "")
        if not ref or not path:
            sys.exit(f"--from needs REF=PATH[:SPEC], got {item!r}")
        by_num, folder = load_cards(path)
        selections.append((ref, by_num, parse_spec(spec, len(by_num))))
        folders[ref] = folder

    out = Path(args.out)
    ledger, start = [], 1
    if args.append and out.exists():
        ledger = yaml.safe_load(out.read_text())["claims"]
        start = max((int(c["id"][1:]) for c in ledger), default=0) + 1
    try:
        claims, cmap = convert(selections, start, args.reviewed_by)
    except KeyError as e:
        sys.exit(str(e))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump({"claims": ledger + claims}, sort_keys=False, width=100, allow_unicode=True))
    mp = out.with_name("claims-map.yaml")
    old = yaml.safe_load(mp.read_text()) if args.append and mp.exists() else {}
    mp.write_text(yaml.safe_dump({**(old or {}), **cmap}, sort_keys=False, width=100, allow_unicode=True))
    if args.pages_root:
        for ref, folder in folders.items():
            dest = Path(args.pages_root) / ref / "pages"
            if (folder / "pages").is_dir() and not dest.exists():
                shutil.copytree(folder / "pages", dest)
    if args.show:
        show(claims)
    print(f"{len(claims)} claims written to {out} ({'verified' if args.reviewed_by else 'unverified'}); map in {mp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
