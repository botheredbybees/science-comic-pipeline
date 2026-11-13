# Visual QA

Date: 2026-11-13. Storyboard: `storyboard.yaml` (6 beats, 36 panels). Rendered with `renderers/xkcd/render.py`, A4, 6 pages.

## Scan (`scripts/visual_qa.py`)
Clean on the final storyboard: `6 page(s), 36 panel(s), 122 text item(s)` / `no defects found`. The first run on a relative
`--keep output/...` path crashed (see SKILL-FEEDBACK.md); re-run with an absolute path. The scan was clean on the first try too (7 pages,
123 text items) even though the pages had defects a person could see, so the by-eye pass found all of the following.

## Pages viewed by eye
All six pages, rendered to PNG with headless Chrome at 794 x 1123, viewed twice (before and after fixes). Caveat: the machine had no Patrick
Hand font, so Chrome drew the SVG in a serif fallback. Text widths are therefore not exactly what the hand font would give; the scan and my
review used the fallback.

## Defects found and fixed (all in the storyboard's staging, none in the renderer)
| page, panel | defect | fix |
|---|---|---|
| 1, B1.1 | sign text "EARTH SYSTEM MODELS: RATES AND FLUXES" ran across the sign's border | shorter label, wider sign |
| 1, B1.3 | narrow panel with a tiny figure in a tall empty box | weight standard, scale 1.5 |
| 1, B2.2 | "more data" label ran under the neighbouring paper | label "more" |
| 3 (was 2), B3.3 | card label "Crocosphaera" at minimum size, "UCYN-A" spilling out of its card | panel weight wide |
| 3, B3.4 | box labels, "is not" and "Genes aren't rates." overlapped boxes and the figure | wide panel, boxes moved to the top, figure scaled down |
| 3, B3.7 | three tiny figures in a small panel | weight standard, scale 1.4 |
| 3, B4.1 | chart notes crowding the chart title | notes moved lower |
| 4, B4.4 | speech line crossed the framed picture | picture moved to the lower middle, line shortened |
| 4, B4.5 | card label "biochemistry" at minimum size | wide panel |
| 4, B4.6 | the solid ">200-fold" bar blacked out the "lowest" and "highest derived rate" labels | hollow bar, plain ticks |
| 4, B4.7 | sign label overflowed the sign | label "omics rates?", wider sign |
| 5, B6.1 | "biogeochemistry" ran over its box's right edge; arrows clumsy | wider boxes, arrows moved |
| 5, B6.5 | board title ran past the board | title "response?" |
| 2, B3.2 | sign label crossed the bottom of the sign | larger sign |

## What is left (known limits, not fixed)
- Character size changes between panels (the same modeller is drawn at scale 0.65 in B3.4 and 1.5 in B1.3) because panel width differs and
  the scene scales with the panel; B1.3 and B3.7 are drawn large on purpose to fill their panels.
- A caption wraps one orphan word onto its own line in B5.5 ("P.") because the line width is estimated, not measured.
- The desk is a plain empty rectangle in several panels; fine for the metaphor, plain as a drawing.
- Dot the diatom is drawn as a loaf-like outline; it is the renderer's diatom shape.
- B1.2's joke is still `keeps_claims_intact: false`, so `validate_storyboard.py --strict` exits 1 with one warning. This is deliberate: a
  human reviewer decides (see CLAIM-CHECK.md).
- The "Condensed into a comic with invented characters and scenes" attribution is on the last page.

## Export
`scripts/export_pdf.py examples/strzepek-2022-rates/storyboard.yaml -o output/strzepek-2022-rates.pdf`: 6 A4 pages; the attribution (title,
authors, year, DOI, "Licence: CC BY 4.0") is printed at the foot of page 6. The PDF is in `output/` (outside the working folder, ignored by git).
