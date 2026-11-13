# Visual QA: lin-2021-wap-sea-ice

Date: 2026-11-13. Storyboard: 59 panels, 11 A4 pages. PDF: `output/lin-2021-wap-sea-ice.pdf` (Patrick Hand embedded, 11 pages,
attribution block complete on page 11: title, authors, year, DOI, licence, two links, "did not write or endorse" line).

## Commands (final runs)

- `visual_qa.py examples/lin-2021-wap-sea-ice/storyboard.yaml --keep output/lin-2021-wap-sea-ice` -> "11 page(s), 59 panel(s), 201 text item(s) / no defects found", exit 0.
- `validate_storyboard.py ... --strict` -> 0 errors, 2 warnings (B4.7 and B6.11: jokes awaiting a human), exit 1 (the right end state).
- `check_quotes.py ... --strict` -> 76 claims, 0 errors, 0 warnings, exit 0.
- `export_pdf.py ... -o output/lin-2021-wap-sea-ice.pdf` -> wrote the PDF, exit 0.
- PNGs for review: `pdftoppm -r 80 -png` (and -r 110 for page 9 charts); every page viewed after the last layout change,
  pages 2, 5, 8, 9, 11 again after the final edits. The sheet (`sheet.html`) has 11 SVG pages like the PDF; the layout was not
  compared visually (page count only).
- The `preview_storyboard.py` HTML was written (exit 0) but was not opened in a browser: the PDF was read instead.

## Defects found by eye (the scan was clean each time except once) and what was done

| page (first render) | panel | defect | fix |
|---|---|---|---|
| 1 | B1.2 | sign text ("Antarctica") ran through the bottom border of the sign | label shortened to "Fastest sea ice decrease", sign made taller |
| 1 | B1.4 | board cards ("gross primary production") shrunk to unreadable size in a narrow panel | panel weight standard -> wide |
| 2 | B2.4 | flow box "water filtered" half covered by Wren's clipboard | flow moved right (x 0.36, w 0.62) |
| 3 | B3.1 | axis title touched the panel border | title shortened to "NCP decreased offshore", panel small |
| 3 | B3.2, after widening B3.4 | scan: overlap "2012 early" / "2013 early" when the panel was squeezed to about 6 units | panel made `wide`, then it fit; a `full` panel had left a half-empty row |
| 3 | B3.4 | hand-hyphenated bar labels ("crypto-phytes") | full words, panel `wide` |
| 5 | B4.1 | `wide` panel was packed at a third of the row; y-label and Wren's clipboard collided with the plot; note wrapped "4 / °C" | weight `full`, plot moved right, note split into two short labels |
| 6 | B5.4 | clipboard overlapped the first flow box | flow moved right |
| 7 | B5.11 | board in a full row with a blank half below | board shortened, Wren and Dot added below it |
| 8 | B5.15 | correlation chart had a scale down to -1 with no negative bars (wasted half the panel) | `min` removed, `max: 1` kept (hidden) |
| 10 | B6.4 | board touched Wren's clipboard | board moved right and narrowed |
| 10 | B6.10 | long caption (40 words) with a tiny figure | panel `wide`; caption kept whole because splitting a conditional would drop its hedge |

## Checked and fine

Reading order; no pages with a large blank band except the last (page 11 is full); no garbled characters (curly quotes,
the minus sign in "-80 °C" and the plus-minus sign render); chart labels, titles and units present; no face implies something
the paper does not say (Teo is "surprised" twice, by 2480 ASVs and by the dimensionality of the dataset, which are the
comic's reactions, and Dot smiles in the joke panel B4.7); bar charts show only values in cited claims; no axis maximum shown that is not cited.

## Left / known limits

- The renderer prints bar values with `%g`: 25.0, 23.0, 14.0 and 19.0 show as 25%, 23%, 14% and 19% (the captions keep the paper's
  figures). Not fixed (not blocking).
- In several panels the figures are small next to a long caption (B4.6, B5.8, B6.10): the caption's height sets the row.
- Text wrapping is by average glyph width, not measured; judged in the PDF.
- Two jokes await a human: B4.7 (Dot's smugness) and B6.11 (Teo's tea beside a caveat). B2.3 (Teo's tea against "-80 °C") was
  checked against the five questions and set `keeps_claims_intact: true`.
