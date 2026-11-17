---
name: overview
description: Use after a comic's claims are verified (ideally after the full comic is finished) to make a one-page version of it that points to the long one. Six or so panels reusing the same verified claims, one printed page, a link to the full comic in the footer. The picture to attach to a post.
---

# One-page overview

**Goal:** a reader who will not open a 40-panel PDF can still get the finding, the caveat and the open question from
one page, and can see where the long version is. It is a comic of its own, not a contact sheet: it has a beginning (a
contrast or a question), a middle (what the studies found) and an end (what the authors say is still open).

**You need:** the full comic's `claims.yaml` (verified), `head.yaml` and `beats/`. The overview is a second storyboard in
`overview/` inside the same folder, **reusing the same ledger**: it adds no claim, so nothing needs verifying twice.

```
examples/<slug>/
  claims.yaml
  head.yaml  beats/  <slug>.pdf          the full comic
  overview/
    head.yaml                            title "<short title>: In Brief", meta.more, left_out, cast
    beats/B01-overview.yaml              one beat, about six panels
    <slug>-overview.pdf   ATTRIBUTION.md
```

## 1. Choose the panels

Take them from the finished comic where you can (copy a panel and give it a new id; its captions already keep the hedge
and the scope), or write new ones to the same rules as `skills/storyboard`. **One panel can carry one finding;** keep:

- the **contrast or question** the paper turns on (what a reader would repeat);
- **one panel per paper or per result** that matters, with its number and its scope ("In Clarke's study…");
- **the authors' own limit**, as in a "Most. Not all." panel: an overview that drops the caveat is a different, stronger
  claim than the paper makes;
- **what the authors say is still open**;
- **a pointer panel**, as the last panel: a character beside a book labelled "the full comic" and saying it is "linked below". Many
  readers will only ever see this page, so the picture itself must say there is more, and where.

Leave out methods, statistics beyond the one number a result needs, and every joke that is not approved. A joke is
the user's call in the overview too.

## 2. Fit one page

The page holds about **two rows of three** panels under the title, with the footer (licence note and links) taking a
fifth of it. So: **one beat** (rows are packed within a beat, so a one-panel beat becomes a full-width row), every panel
`weight: small` and `height: short`, no `full` panel, and about six panels in all (two rows of three; a seventh panel, or any `full` or one-panel row, pushes the footer onto a second page). If the PDF runs to a second page,
cut a panel; do not shrink the type. Keep the title to one line.

## 3. Point at the long version

In `overview/head.yaml` set where the full comic lives; the footer prints it as a link above the paper's own:

```yaml
meta:
  more: { text: "The full comic, with the methods, the numbers and the authors' caveats", url: "https://.../<slug>.pdf" }
```

Use the address a reader can open: for a public example, the file in the repository. A private comic has no public
address and its overview is private too (`meta.private`); leave `more` out and never publish either. Say in `meta.left_out`
that this is the short version and what the full comic adds.

## 4. Build and check, the same as any comic

```
python scripts/build_storyboard.py examples/<slug>/overview --claims examples/<slug>/claims.yaml
python scripts/validate_storyboard.py --strict --variety examples/<slug>/overview/storyboard.yaml
python scripts/check_quotes.py examples/<slug>/overview/storyboard.yaml --pages-root sources --strict
python scripts/visual_qa.py examples/<slug>/overview/storyboard.yaml        # must say 1 page
python scripts/export_pdf.py examples/<slug>/overview/storyboard.yaml -o examples/<slug>/overview/<slug>-overview.pdf
```

Look at the page itself (a PNG of it, with `pdftoppm -r 80 -png`), as in `skills/visual-qa`: a label clipped at a
panel's foot, or a caption that does not match its picture, is not something the scan finds. `--claims` is needed every
time you build the overview, because its ledger is one folder up. Write a short `overview/ATTRIBUTION.md` that points to
the full comic's.

`pdftoppm -r 130 -png -singlefile <pdf> <name>` makes the PNG to attach to a post. Then link it from `PROMO.yaml` (`overview:`; see `skills/promote`): it is the picture to attach to a post.
