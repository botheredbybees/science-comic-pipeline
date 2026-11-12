# Renderers

A renderer turns a validated `storyboard.yaml` into pages. One exists so far.

## What a renderer does

- Reads the storyboard only. It never opens the source paper.
- Draws each panel's `scene`, `speech`, `frame` and `staging`. It adds no facts.
- Lays panels out with `scripts/layout.py` (rows of at most three, no blanks, widths from `weight`).
- Keeps text as real text (SVG `<text>`), so it can be checked and edited.
- Gives every panel an accessible description (its scene text).
- Prints the source's attribution on the last page, built from `meta.source`. Licences such as
  CC BY require it.

## Staging

A sentence cannot be drawn by a program, so a panel can carry a `staging` block: who stands where
(`characters`: cast id or `extra`, `x`, `pose`, `face`, `facing`, `holding`, `scale`) and which
props appear (`props`: `board`, `slide`, `bars`, `paper`, `phone`, `bowl`, `wall`, `sign`,
`picture` (a small nested staging), `desk`, `label`, `arrow`, `box`). Positions are fractions of the
panel's scene area. In the pipeline the agent writes the staging as the "artist" step. Numbers
in a chart or label need a claim, exactly as dialogue does. A panel without staging falls back to
its scene text. Cast members may carry `appearance` hints (`hair`, `glasses`, `lanyard`).

## xkcd (`renderers/xkcd/render.py`)

Stick figures, outlined and borderless panels, a hand-drawn wobble on every line, a short line from
speech to speaker instead of a balloon, grey caption strips, almost no colour.

```bash
python renderers/xkcd/render.py examples/akam-2026-cartooning/storyboard.yaml -o output/xkcd
```

It writes `page-1.svg` ... (A4, 1000 units wide) and `sheet.html`, a page to look at them. The
wobble is seeded geometry, so the output is identical on every run and survives PDF converters.
It tries panels at several heights and keeps the tallest setting that needs the fewest pages.

Known limits:
- Text is wrapped with an average glyph width, not measured, so a different font may need a
  small margin. The face is Patrick Hand (SIL Open Font Licence); the SVG falls back to
  Comic Neue, Comic Sans MS, then any cursive face.
- Figures scale with the panel's height, so they look small in wide, short panels.
- Pagination never splits a row, and packing runs per beat.

## Planned

| Style | Notes |
|---|---|
| `painted/` | Layered, textured SVG in the manner of a ligne-claire or Franco-Belgian album. Expensive to author by hand; may need an image model. |
