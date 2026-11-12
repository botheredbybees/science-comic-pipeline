#!/usr/bin/env python3
"""Assemble storyboard.yaml from a working folder.

A working folder holds
  head.yaml            version, meta (title, source, spine) and cast
  beats/B*.yaml        a list of beats, each a list of panels (sorted by file name)
  claims*.yaml         ledgers (a `claims:` list); also any claims/*.yaml
and the output keeps only the claims the panels actually cite, so a long ledger can serve several
comics. It reports any cited claim that is not `verified`.

    python scripts/build_storyboard.py examples/lin-2017-wap-npc
"""
import argparse
import glob
import sys
from pathlib import Path

import yaml


def build(folder):
    folder = Path(folder)
    head = yaml.safe_load((folder / "head.yaml").read_text())
    beats = []
    for f in sorted(glob.glob(str(folder / "beats" / "B*.yaml"))):
        beats += yaml.safe_load(Path(f).read_text())
    ledger = {}
    for f in sorted(glob.glob(str(folder / "claims*.yaml")) + glob.glob(str(folder / "claims" / "*.yaml"))):
        for c in (yaml.safe_load(Path(f).read_text()) or {}).get("claims", []):
            if c["id"] in ledger:
                raise ValueError(f"claim {c['id']} appears in more than one ledger file")
            ledger[c["id"]] = c
    used = sorted({cid for b in beats for p in b["panels"] for cid in p.get("claim_ids", [])}, key=lambda s: int(s[1:]))
    missing = [c for c in used if c not in ledger]
    if missing:
        raise ValueError(f"panels cite claims that are not in any ledger: {missing}")
    doc = dict(head)
    doc["claims"] = [ledger[c] for c in used]
    doc["beats"] = beats
    return doc, [c for c in used if ledger[c]["status"] != "verified"], len(ledger)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("folder")
    ap.add_argument("-o", "--out", help="default: <folder>/storyboard.yaml")
    args = ap.parse_args(argv)
    doc, unverified, n_ledger = build(args.folder)
    out = Path(args.out or Path(args.folder) / "storyboard.yaml")
    out.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=200))
    panels = sum(len(b["panels"]) for b in doc["beats"])
    print(f"{len(doc['beats'])} beats, {panels} panels, {len(doc['claims'])} of {n_ledger} ledger claims used"
          + (f"; NOT verified but used: {unverified}" if unverified else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
