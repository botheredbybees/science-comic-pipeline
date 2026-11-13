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
`sign`, `desk`, `flash`, `cups`, `picture` (a small nested staging), `label`, `arrow`, `box`, `laptop`, `microscope`, `teapot`, `net`, `thermometer`; charts
and diagrams `bars`, `plot`, `axis`, `pie`, `flow`, `steps`, `stack`). Positions are fractions of the
panel's scene area. In the pipeline the agent writes the staging as the "artist" step. Numbers
in a chart or label need a claim, exactly as dialogue does. A panel without staging falls back to
its scene text. Cast members may carry `appearance` hints (`body`: stick, diatom, krill, penguin or whale, `hair`, `glasses`, `coat`). `hair` is `none`, `bob`, `long`, `ponytail`, `bun`, `spiky` or `beanie`: solid black hair laid over the head (the face is what it leaves uncovered), or a plain white hat that overhangs the head, each one big simple shape with no detail, as in a newspaper-strip stick figure. `hair_tone: light` draws the same shape as an outline with no fill, and `hair_tone: strands` draws it as a handful of curved strokes combed back from a parting (both read as blond; neither suits `spiky`, which is always solid). `coat: true` puts a lab coat on the figure (an outline round the torso with a V collar and a pocket). The animal bodies are drawn in `renderers/xkcd/animals.py`; a krill is small, so give it a larger `scale` in the staging (about 1.3 to 1.5), and a whale a smaller one (about 0.4 to 0.65).
On an `axis`, `row` stacks crowded labels at different heights. A `bars` prop draws its `title` above the chart; its
bars stand on a zero line, and a negative value hangs below it (a signed index such as Ivlev's: set `min: -1`, `max: 1`).
Each chart is scaled to its own largest bar unless `max` is given, so bar heights are not comparable between panels;
say so in the caption or give them the same `max`. Axis tick numbers (and a `min` or `max` shown on bars) count as numbers
for the validator: cite the claim that defines the scale.

Things found by using the vocabulary (check the render when you stage these): a character `holding` can only be
a `marker`, `mug` (held by its handle, with steam), `teacup` (a cup and saucer with a tea-bag tag), `paper`, `clipboard`, `notebook`, `flask` or `magnifier`; a `sign`'s text sits in the top half of its `h` (the lower half is the post); a
`label`'s `x` is its centre; an `arrow` is drawn from `x`, `y` to `x2`, `y2`; a `board` shrinks its card text
in a narrow panel (to about 9 units); a solid `axis` bar can cover its tick labels; `year` in `meta.source`
is an integer.

## Character vocabulary

A staged character takes `pose`, `face` and `facing`; the enums are in the schema and repeated here.

| Field | Values |
|---|---|
| `pose` | `stand`, `point` (front arm out), `hold` (something held out at chest height), `think` (hand to the chin; with something in the hand it becomes `hold`), `shrug` (both hands up and out), `sip` (a hand raised to just in front of the mouth), `up` (both arms raised) |
| `face` | `neutral`, `smile`, `worry`, `deadpan`, `surprised` |
| `facing` | `right` (the default) or `left` |
| `holding` | `marker`, `mug`, `teacup`, `paper`, `clipboard`, `notebook`, `flask`, `magnifier` |
| `scale` | a multiplier; about 1.0 for people, 1.0 to 1.5 for krill, 0.4 to 0.65 for a whale |
| `body` | overrides the cast member's body, so an `extra` can be an animal |

A character's look (hair, hair tone, glasses, coat, body) belongs to the cast member in `head.yaml`; see the appearance
options above. Wording a label: use `box` for a multi-word label (it wraps inside its border) and `sign` for a short one.
A number prints the way YAML reads it: `25.0` stays `25.0` and `17.5` stays `17.5`, but `17.60` is read as `17.6`, so put the
exact figure in the caption.

## Prop fields

Every prop has `kind`, and `x`, `y`, `w`, `h` as fractions of the scene (`w` and `h` default to about 0.3). A number that is
drawn (a bar value, a pie value, a tick, a note label) must come from a cited claim, and is printed as written (`25.0`
stays `25.0`).

| `kind` | Fields it reads |
|---|---|
| `bars` | `bars` (each `label`, `value`, `style`: solid or hollow); `title`; `unit` (`%` adds a percent sign); `max`, `min` (the scale; `min` below zero hangs negative bars under a zero line); `show_values` and `show_max` (false hides the numbers and the top tick) |
| `axis` | `items`: each `label`, `at` (0 to 1 along the line); `to` (a span from `at` to `to`); `style` (`solid`, `hollow` or `mark`, a dot); `row` (0 to 3, lifts crowded labels); `title` |
| `plot` | `series`: each `points` (a list of `[x, y]` in 0 to 1, y up) and `style` (solid, dashed, dotted); `notes`: each `x`, `y`, `label`; `x_label`, `y_label`, `title`. A schematic curve should be dashed and the panel should say so |
| `pie` | `items`: each `label`, `value` (shares are drawn in proportion to the values) |
| `flow` | `items`: each `label`; boxes joined by arrows, left to right in a wide box, top to bottom in a tall one |
| `steps` | `items`: each `label`, `caption`; a rising staircase |
| `stack` | `items`: each `label`, `value`, `style`; a column of segments, bottom to top |
| `board` | `cards`: each `label`, `covered` (a hatched, hidden card); `title`; labels shrink to fit |
| `slide`, `paper`, `sign`, `box`, `label`, `picture` | `label` or `title`; `picture` takes a nested `staging`; `label`'s `x` is its centre and `size` is small, normal or large |
| `arrow` | from `x`, `y` to `x2`, `y2` |
| `desk`, `ship`, `bowl`, `bottle`, `jar`, `flash`, `cups`, `phone`, `wall`, `laptop`, `microscope`, `teapot`, `net` (a plankton net), `thermometer` | objects; `label` where one is shown; `cups` takes `items` with a `value` (how full). `laptop`, `microscope`, `teapot`, `net` and `thermometer` keep their proportions inside the box you give them |

**How wide a panel gets.** A panel's `weight` is a preference: `small`, `standard` and `wide` are packed into rows by the
layout, so a `wide` chart can still land at a third of a row. Only `full` always spans the page. Give a crowded chart
`full`, or `height: tall`, and look at the page.

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
