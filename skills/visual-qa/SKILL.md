---
name: visual-qa
description: Use after the storyboard validates and before sharing. Renders the comic, runs the overflow and overlap scan, exports the PDF, and reviews the pages by eye for what a script cannot see; fixes each defect in the storyboard's staging.
---

# Visual QA

**Goal:** a list of defects, fixed, so that the pages read well. A script catches some defects; the rest
need eyes. Do both.

**You need:** a storyboard that validates with no errors (jokes awaiting review may still warn); Chrome or Chromium installed
(used headless; the handwriting font Patrick Hand should be installed or loaded, or text widths differ); a way to view a rendered page as an image (any browser or screenshot tool).

## 1. Scan

```bash
python scripts/visual_qa.py examples/<slug>/storyboard.yaml --keep output/<slug>
```

It reports **overflow** (text past the page edge) and **overlap** (text boxes crossing), by page and
panel, and exits 1 when there is any. Fix each, then re-run until it says `no defects found`.

## 2. Look at every page

Export the PDF first (step 4) and view each page at readable size: it is drawn in the real font, which a bare
`page-N.svg` is not (the SVG shows a fallback font, so wrapping looks different). Without a PDF viewer, make PNGs with
`pdftoppm -r 70 -png examples/<slug>/<slug>.pdf output/<slug>/q`. Compare the PDF with the sheet once: the layout must match.
The scan cannot see the following, so check them yourself, page by page:

- Text running over a drawing, a speech line that crosses a figure, or a line that points at the wrong speaker.
- A figure cut off at a panel edge, or tiny in a wide, short panel.
- Charts: every bar and point labelled; no label cut short; axes and units readable; nothing drawn that
  is not in a claim.
- Pie, axis and flow labels that collide. On a crowded `axis` a `row` lifts each label relative to its own height,
  so labels of different heights cross each other's leader lines: give each cluster of marks one combined label instead.
- Charts with no title, no unit, or a bar label touching the top of a solid bar (the scan sees text against text only).
- A caption in a font size different from its neighbours, or text too small to read at A4.
- Reading order: left to right, then down. Two rows made only of open (borderless) panels adjacent, or two
  rows with the same widths, make a page hard to read.
- Pages with a big blank band at the bottom (except the last), or a last page nearly empty.
- Text running through the border of its own sign or box (the scan compares text with other text only).
- Garbled characters (accents, quotes, "mojibake").
- Faces and poses that imply something the paper does not say (a worried animal).

Write each defect down: page, panel, what, and the fix.

## 3. Fix in the storyboard, not by hand

Most defects are fixed in `staging` or on the panel:

| Defect | Try |
|---|---|
| Text over a drawing | move the prop or character (`x`, `y`, `w`, `h`), change `scale`, or shorten the caption |
| Figure tiny in a wide panel | make the panel `standard` or `height: tall` |
| Crowded chart labels | `row` on an `axis`, fewer labels, a `wide` or `full` panel |
| Two open rows adjacent / same-width rows | change a panel's `frame` or `weight` |
| Blank band under a page | `height: tall` on a significant panel (the layout repacks, so look at the next page too) |
| A caption too long | split into two panels |

If the cause is a renderer bug (a prop that cannot be staged correctly), fix `renderers/xkcd/` and add a
test in `tests/test_xkcd.py` that fails before the fix.

After every change, re-run the validator, the scan and look again. Do not stop at the first clean scan:
a fix can create a new defect.

## 4. Export

```bash
python scripts/export_pdf.py examples/<slug>/storyboard.yaml -o examples/<slug>/<slug>.pdf
```

One A4 page per comic page. The PDF is the finished comic and lives in the example's folder, where git keeps it (`output/` is not kept). Check the page count and that the attribution for the source is printed on
the last page, complete: title, authors, year, DOI, licence, and two clickable links (the original paper and the licence terms), and the line that the comic
is an adaptation the authors did not write or endorse.

## Output

`QA.md` in the working folder (or your reply): the defects found, what you did, and what is left (known
limits, such as text wrapped by average glyph width, not measured). **Done when** the scan is clean, you
looked at every page, and the PDF is exported.
