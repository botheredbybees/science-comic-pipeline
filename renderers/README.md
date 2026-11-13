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
props appear (`props`: objects `board`, `slide`, `paper`, `phone`, `bowl`, `bottle`, `jar`, `ship`,
`sign`, `desk`, `flash`, `cups`, `picture` (a small nested staging), `label`, `arrow`, `box`; charts
and diagrams `bars`, `plot`, `axis`, `pie`, `flow`, `steps`, `stack`). Positions are fractions of the
panel's scene area. In the pipeline the agent writes the staging as the "artist" step. Numbers
in a chart or label need a claim, exactly as dialogue does. A panel without staging falls back to
its scene text. Cast members may carry `appearance` hints (`body`: stick, diatom, krill, penguin or whale, `hair`, `glasses`, `lanyard`). `hair` is `none`, `bob`, `long`, `ponytail`, `bun`, `spiky` or `beanie`: solid black hair laid over the head (the face is what it leaves uncovered), or a plain white hat that overhangs the head, each one big simple shape with no detail, as in a newspaper-strip stick figure. `hair_tone: light` draws the same shape as an outline with no fill (blond). A `lanyard` is a name badge on a short cord, and `coat: true` puts a lab coat on the figure (an outline round the torso with a V collar and a pocket). The animal bodies are drawn in `renderers/xkcd/animals.py`; a krill is small, so give it a larger `scale` in the staging (about 1.3 to 1.5), and a whale a smaller one (about 0.4 to 0.65).
On an `axis`, `row` stacks crowded labels at different heights. A `bars` prop draws its `title` above the chart; its
bars stand on a zero line, and a negative value hangs below it (a signed index such as Ivlev's: set `min: -1`, `max: 1`).
Each chart is scaled to its own largest bar unless `max` is given, so bar heights are not comparable between panels;
say so in the caption or give them the same `max`. Axis tick numbers (and a `min` or `max` shown on bars) count as numbers
for the validator: cite the claim that defines the scale.

Things found by using the vocabulary (check the render when you stage these): a character `holding` can only be
a `marker`, `mug` or `paper`; a `sign`'s text sits in the top half of its `h` (the lower half is the post); a
`label`'s `x` is its centre; an `arrow` is drawn from `x`, `y` to `x2`, `y2`; a `board` shrinks its card text
in a narrow panel (to about 9 units); a solid `axis` bar can cover its tick labels; `year` in `meta.source`
is an integer.

## xkcd (`renderers/xkcd/render.py`)

Stick figures, outlined and borderless panels, a hand-drawn wobble on every line, a short line from
speech to speaker instead of a balloon, grey caption strips, almost no colour.

```bash
python renderers/xkcd/render.py examples/akam-2026-cartooning/storyboard.yaml -o output/xkcd
```

It writes `page-1.svg` ... (A4, 1000 units wide) and `sheet.html`, a page to look at them. The
wobble is seeded geometry, so the output is identical on every run and survives PDF converters.
It tries panels at several heights and keeps the tallest setting that needs the fewest pages.

**Row heights.** Once the pages are split, each page's spare height is shared out among its rows, so
pages end at the bottom margin and rows differ in height. The richest rows (charts, a full-width panel,
many props) get the most room, and the plainest conversational rows give a little up. A panel may say
`height: tall` for a significant beat or `height: short` for a quick one, which scales its row's share
(a row is tall if any of its panels is, and short only if all are). A sparse last page is left alone
instead of being stretched to fill the sheet.

**Rows that read as a layout, not a grid.** The row packer is nudged away from repeating the widths of the
row before it (identical widths cost more than near-identical), including across a beat boundary, so
pages are not a stack of equal rows. And two rows made only of open (borderless) panels run together and
blur the reading order, so when a row would follow another all-open row, its widest panel is outlined
(the storyboard itself is not changed).

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
