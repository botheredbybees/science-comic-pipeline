# Visual QA

Run 2026-11-13 on `examples/pauli-2021-krill-salps-diet/storyboard.yaml` (46 panels, 9 pages, black and white xkcd renderer). Pages were viewed one by one as PNG screenshots of each SVG (headless Chrome, 794 x 1123), after every round of fixes.

## Final state

- `visual_qa.py --keep output/pauli-2021-krill-salps-diet`: "9 page(s), 46 panel(s), 177 text item(s); no defects found", exit 0.
- `export_pdf.py ... -o output/pauli-2021-krill-salps-diet.pdf`: 9 pages (pdfinfo). Last page carries the source attribution ("Adapted from ... doi ... Licence: CC BY 4.0. Condensed into a comic with invented characters and scenes; the authors did not write or endorse it.").
- `validate_storyboard.py --strict`: 0 errors, 2 warnings, both "joke on a panel that cites C58 / C63", i.e. the two jokes awaiting a human.

## Defects found and what was done

| Page, panel | Defect | Fix |
|---|---|---|
| p6, B4.2 | Scan: 2 text overlaps among the crowded Ivlev labels (small flagellates / Chrysophyceae; Pelagophyceae / Prymnesiophytes). Leader lines crossed lower labels even after `row` stacking. | One combined label per cluster ("preferred: ..." and "avoided: ..."), the other dots unlabelled. Scan clean. |
| p6, B4.2 (first attempt) | A long combined label wrapped to many lines and ran past the panel top (scan: overflow). | Kept it at row 0 so it sits just above the axis. |
| p1, B1.1 | Ship hull ran behind Sal; krill overlapped Sal's legs at scale 1.4. | Ship moved right and smaller; krill scale 1.2, Sal moved right. |
| p1, B1.2 | Whale, krill and penguin touching at scale 0.5 / 1.4. | Whale 0.45, krill left at 1.4 only where there was room. |
| p1, B1.5 | The bar for the shift was a heavy black slab. | `style: hollow`. |
| p2, B1.7 | Krill touched the bowl. | Bowls moved right; Kip scale 1.2. |
| p2 | Large blank band under the ship panel. | `height: tall` on B2.1, which absorbed it. |
| p3 to p7 | Chart `title` is accepted by the schema and counted by the validator but **not drawn** for `bars` (B2.4, B3.1, B3.3, B3.4, B3.6, B5.1, B5.2). | Each title is now a separate `label` prop above the chart. Recorded as a renderer gap, not fixed there. |
| p5, B3.4 | Bar labels "dinoflagellates (Dinophyceae)" and "crustaceans" ran into each other. | Label shortened to "other dinoflagellates". |
| p5, B4.1 | Axis panel mostly empty. | `height: short`; B4.2 and B4.3 lost their `tall` hints. |
| p6, B4.4 | The caption wraps "200 / m". A no-break space in the caption text did not prevent it (the wrapper splits on it). | Left. Minor. |
| p8, B6.2 | Sal faced the direction of the arrow, drawing forward swimming for "back-flush". | Sal faces left, arrow points right, scale 1.3. |
| p9, B6.5 | Mara drawn small and floating above the bowl. | Mara removed from the panel (scene text updated). |
| p6, B4.5 | Kip smiled as well as Sal, which reads as smugness the paper does not report. | Kip made neutral; only Sal smiles (the joke). |

## Looked at and left

- **Bar value labels touch the top of tall solid bars** on p4 and p5 (e.g. "19.4%", "12.2%"); still readable. A renderer detail.
- **Charts are not on a common scale** across panels (each chart's axis maximum is its own largest bar, shown as a number in a claim). Bar heights should not be compared between panels; the captions carry the numbers.
- **Krill drawn horizontally** and larger than the people at scale 1.0 to 1.4; the skill's 1.3 to 1.5 recommendation makes a krill as wide as a third of a standard panel, so 1.0 to 1.2 was used where figures stand close.
- **Salps are plain stick figures**, so nothing shows what a salp looks like (see CLAIM-CHECK.md).
- **Back-flushing (B6.2)** is a stick figure and a single arrow: it does not show a jet out of the front opening. Honest to the claim but weak as a picture.
- **The 9 pages** run to the bottom margin except the last, which is about two thirds full.
- **Patrick Hand is not installed on this machine** (`fc-list | grep -i patrick` finds nothing, no Comic Neue or Comic Sans either), so every screenshot and the PDF use the renderer's final fallback, a serif face, not the handwriting look the renderer intends. Text is wrapped by average glyph width, not measured, so widths with Patrick Hand may differ; the scan was not re-run with the font installed. The skill says the font "should be installed or loaded" but not how or where to get it.
- **Alt text:** every `scene` was re-read against the staging. Fixed in B1.8 (said "board", none staged), B1.1 (ship is staged), B6.2 and B6.5.

## PDF check

`pdftoppm -r 60` on `output/pauli-2021-krill-salps-diet.pdf` and a contact sheet of the 9 pages: same layout and page breaks as the SVG pages, attribution on page 9. Only checked at low resolution, so fine text was not re-read on the PDF. The PDF text looks like a different face from my SVG screenshots (which used a serif fallback), so the PDF export and a plain Chrome screenshot do not pick the same font on this machine.
