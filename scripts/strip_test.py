#!/usr/bin/env python3
"""EXPERIMENT. The strip test: read a comic's words with the pictures taken away, and see whether the words still carry each panel's claims.

    python scripts/strip_test.py examples/<slug>/storyboard.yaml [-o strip.md]

From the comic lore (Part E): "read the captions and breakout boxes alone; if they do not carry the claim, the dressing is hiding a hole".
This prints the words of every panel in reading order (captions, speech, and the text printed in props: labels, boxes, board cards, chart titles and bar names),
then checks each panel against the claims it cites:
  * **numbers**: each number in a cited claim should appear in the panel's words. A number that appears only as a chart value (a bar's height) is carried
    by the picture, not the words;
  * **terms**: the share of the claim's content words (longer than four letters, not a stop word) found in the panel's words, so a panel whose words
    say nothing about its claim stands out.
A panel is flagged when a claim's numbers are missing from its words, or when its words share under a quarter of a claim's terms. These are signals to
look at the panel, not verdicts: a short caption may rightly carry a long claim by shortening it, and a chart may rightly carry a number. A panel with no
words and no claims is listed separately. The check reads only the storyboard; it does not look at the picture.
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from suggest_graphics import numbers_in  # noqa: E402

STOP = set("""about above after again against also because been before being between both could does doing during each from have having into more most only other over same
should since some such than that their them then there these they this those through under until very were what when where which while with without would""".split())
FLAG_TERMS = 0.25


def prop_words(prop):
    """Text printed by a prop (and by pictures inside it): labels, titles, box text, card labels, item and bar labels. Chart values are returned separately."""
    words, values = [], []
    for key in ("label", "title", "x_label", "y_label", "unit"):
        if isinstance(prop.get(key), str):
            words.append(prop[key])
    for key in ("items", "cards", "bars", "series"):
        for it in prop.get(key) or []:
            if isinstance(it, dict):
                if isinstance(it.get("label"), str):
                    words.append(it["label"])
                if "value" in it:
                    values.append(str(it["value"]))
    sub = prop.get("staging")
    if sub:
        w, v = staging_words(sub)
        words += w
        values += v
    return words, values


def staging_words(st):
    words, values = [], []
    for pr in (st or {}).get("props", []):
        w, v = prop_words(pr)
        words += w
        values += v
    for half in (st or {}).get("split", []) or []:
        w, v = staging_words(half)
        words += w
        values += v
    words += [s for s in (st or {}).get("split_labels", []) or [] if s]
    return words, values


def panel_text(panel):
    """(words, chart values): the words a reader reads in this panel, and the numbers printed only as chart values."""
    words = [s["text"] for s in panel.get("speech", []) if s.get("text")]
    w, v = staging_words(panel.get("staging"))
    return words + w, v


def nums(text):
    """The numbers in a text for this check: not the figure in a name such as 18S or 16S rRNA, and without a sentence's full stop stuck to the end."""
    return {n.rstrip(".") for n in numbers_in(re.sub(r"\b\d+(?=[A-Za-z]\b)", "", str(text)))} - {""}


def terms(text):
    return {t for t in re.findall(r"[a-z]{5,}", str(text).lower()) if t not in STOP}


def check_panel(panel, claims):
    """Return a list of (claim id, problem) for the panel; empty if its words carry every cited claim."""
    words, values = panel_text(panel)
    blob = " ".join(words)
    have_nums, have_terms = nums(blob), terms(blob)
    chart_nums = set().union(*(nums(v) for v in values)) if values else set()
    out = []
    for cid in panel.get("claim_ids") or []:
        c = claims.get(cid)
        if not c:
            continue
        want_nums = nums(c["text"])
        missing = sorted(want_nums - have_nums)
        if missing:
            picture = [m for m in missing if m in chart_nums]
            out.append((cid, f"number(s) {', '.join(missing)} not in the words" + (f" (only {', '.join(picture)} as a chart value)" if picture else "")))
            continue
        want_terms = terms(c["text"])
        if want_terms and len(want_terms & have_terms) / len(want_terms) < FLAG_TERMS:
            out.append((cid, f"the words share {len(want_terms & have_terms)} of {len(want_terms)} terms of the claim"))
    return out


def run(doc):
    claims = {c["id"]: c for c in doc.get("claims", [])}
    rows, flagged, silent, cited = [], [], [], 0
    for beat in doc["beats"]:
        for p in beat["panels"]:
            words, _ = panel_text(p)
            problems = check_panel(p, claims)
            cited += bool(p.get("claim_ids"))
            rows.append((beat, p, words, problems))
            if problems:
                flagged.append((p["id"], problems))
            if not words:
                silent.append(p["id"])
    return rows, flagged, silent, cited


def render(doc, source):
    rows, flagged, silent, cited = run(doc)
    out = [f"# Strip test: {doc['meta'].get('title', source)}", "",
           "_An experiment. The words of every panel with the pictures taken away, then what the check found. Signals to look at, not verdicts._", "",
           f"{len(rows)} panels, {cited} citing a claim; **{len(flagged)} flagged**, {len(silent)} with no words.", ""]
    if flagged:
        out += ["## Flagged panels", ""] + [f"- **{pid}**: " + "; ".join(f"{cid}: {why}" for cid, why in probs) for pid, probs in flagged] + [""]
    if silent:
        out += [f"## Panels with no words: {', '.join(silent)}", ""]
    out += ["## The words, in reading order", ""]
    last = None
    for beat, p, words, problems in rows:
        if beat["id"] != last:
            out += [f"### {beat['id']} {beat.get('title', '')}", ""]
            last = beat["id"]
        flag = " **[flagged]**" if problems else ""
        out.append(f"- **{p['id']}** ({', '.join(p.get('claim_ids') or []) or 'no claim'}){flag}: " + (" / ".join(w.replace("\n", " ") for w in words) or "_no words_"))
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("storyboard")
    ap.add_argument("-o", "--out", help="write the report here (Markdown); default: print it")
    args = ap.parse_args(argv)
    doc = yaml.safe_load(Path(args.storyboard).read_text())
    text = render(doc, args.storyboard)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text)
        rows, flagged, silent, cited = run(doc)
        print(f"{len(rows)} panels, {len(flagged)} flagged, {len(silent)} with no words -> {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
