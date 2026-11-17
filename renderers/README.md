# Renderers

A renderer turns a validated `storyboard.yaml` into pages. One exists so far.

## What a renderer does

- Reads the storyboard only. It never opens the source paper.
- Draws each panel's `scene`, `speech`, `frame` and `staging`. It adds no facts.
- Places each speech line above its speaker's head, then moves it off any prop it would cross: it slides to the free side of the prop, or is wrapped narrower to fit the gap (a narrower line is taller, so the scene gets a little shorter). A speaker standing in front of a prop, a gap under about a dozen characters wide, and backdrops (`desk`, `seaice`, `iceshelf`, `mixedlayer`, `skyline`, `livingroom`, `stage`) leave the line where it was. Props are measured by what they draw, not by the box you gave them. Characters other than the speaker are not checked.
- Lays panels out with `scripts/layout.py` (rows of at most three, no blanks, widths from `weight`).
- Keeps text as real text (SVG `<text>`), so it can be checked and edited.
- Gives every panel an accessible description (its scene text).
- Prints the source's attribution on the last page, built from `meta.source`. Licences such as
  CC BY require it.

## Staging

A sentence cannot be drawn by a program, so a panel can carry a `staging` block: who stands where
(`characters`: cast id or `extra`, `x`, `pose`, `face`, `facing`, `holding`, `scale`) and which
props appear (`props`: objects `board`, `paper`, `bowl`, `bottle`, `jar`, `ship`,
`desk`, `flash`, `cups`, `picture` (a small nested staging), `label`, `arrow`, `box`, `laptop`, `microscope`, `teapot`, `net`, `thermometer`; charts
and diagrams `bars`, `plot`, `axis`, `pie`, `flow`, `steps`, `stack`). Positions are fractions of the
panel's scene area. In the pipeline the agent writes the staging as the "artist" step. Numbers
in a chart or label need a claim, exactly as dialogue does. A panel without staging falls back to
its scene text. Cast members may carry `appearance` hints (`body`: stick, diatom, krill, penguin, whale, salp, copepod, fish, worm, jellyfish, urchin, seal, seabird, moss, bacterium, seastar, dinoflagellate, squid or amphipod, `hair`, `glasses`, `coat`). `hair` is `none`, `short`, `bob`, `shoulder` (to the shoulders), `long` (well past them), `ponytail`, `bun` (grey hair only: it does not read well in other tones), `spiky`, or a hat: `beanie`, `hardhat` (a dome with a brim; it covers the hair), `beret` (a soft flat disc with a stalk), `boater` (a flat-topped crown with a wide flat brim and a band) or `flatcap` (a low dome with a short peak): solid black hair laid over the head (the face is what it leaves uncovered), or a plain white hat that overhangs the head, each one big simple shape with no detail, as in a newspaper-strip stick figure. `hair_tone: light` draws the same shape as an outline with no fill (it reads as blond; it does not suit `spiky`, which is always solid). `hair_tone: grey` fills the shape with the palette's mid grey, for older hair. A `beret`, `boater` or `flatcap` takes the tone as its colour: `dark` is black, `light` is white, `grey` is grey (so a black boater and a white one are one hat in two tones). `head_scale` (0.8 to 1.6, default 1.2) draws a bigger or smaller head on the same body, the face and hair scaling with it; the original size is 1.0. Hats are drawn smaller than the head and tilted, as they are worn. `coat: true` puts a lab coat on the figure (an outline round the torso with a V collar and a pocket). `outfit` puts work clothing on instead of the lab coat: `floatcoat` (a chunky near-black float jacket with a collar, waist strap and reflective patches, for a ship's deck), `parka` (a quilted jacket with the hood up, a furred ring round the face, for the ice) or `hivis` (a sleeveless mid-grey vest with white reflective bands). Everything is black, white and grey: there is no colour in the renderer. The animal bodies are drawn in `renderers/xkcd/animals.py`; a krill is small, so give it a larger `scale` in the staging (about 1.3 to 1.5), and a whale a smaller one (about 0.4 to 0.65). The copepod (about 1.0, seen from above with long antennae, so give it room above and below), fish (1.0), worm (0.8 to 1.0, it is long), jellyfish (0.9), urchin (1.0), seal (0.9, it lies on its belly), seabird (1.0), moss (1.0, a low patch with no face), bacterium (1.2), sea star (1.0), dinoflagellate (1.0, drawn after a horned Ceratium), squid (0.9, swimming to the right, with two long feeding tentacles) amphipod (1.1, a humped sideways-flattened shrimp-like crustacean) and puppet (0.9, a grey rod puppet with button eyes, round ears and a cuff, held up on a stick with no hand drawn) are generic cartoon shapes, not anatomy and not to scale: a caption carries any claim about the real animal, and the cast `role` says it is a stand-in. They take `face` (the eye and a small mouth; the moss, sea star, urchin, jellyfish and dinoflagellate have none and ignore it) and `facing`, and ignore `pose` and `holding`. A copepod, worm, jellyfish or urchin is the right picture for a plankton or benthos paper's organisms; a fish stands in for any bony fish.
On an `axis`, `row` stacks crowded labels at different heights. A `bars` prop draws its `title` above the chart; its
bars stand on a zero line, and a negative value hangs below it (a signed index such as Ivlev's: set `min: -1`, `max: 1`).
Each chart is scaled to its own largest bar unless `max` is given, so bar heights are not comparable between panels;
say so in the caption or give them the same `max`. Axis tick numbers (and a `min` or `max` shown on bars) count as numbers
for the validator: cite the claim that defines the scale.

Things found by using the vocabulary (check the render when you stage these): a character `holding` can only be
a `marker`, `mug` (held by its handle, with steam), `teacup` (a cup with a tea-bag tag), `clipboard`, `flask` or `magnifier`; a `box` grows taller than its `h` if its words need it and centres them; a
`label`'s `x` is its centre and it does **not** wrap (a long one is cut off at the panel edge: use `box`); an `arrow` is drawn
from `x`, `y` to `x2`, `y2`; a `board` shrinks its card text in a narrow panel (to about 9 units) and is unreadable
with more than three cards or a clause on a card (use `box` props); `steps` labels and captions wrap, but keep the labels
short; a `bottle` (0.55 wide to 1) and a `jar` (0.8 to 1) keep their shape in any box and put their `label` underneath,
inside the box you give; `laptop`, `microscope`, `teapot` and `thermometer` keep theirs too; a solid `axis` bar can
cover its tick labels; `year` in `meta.source` is an integer; `meta.source.page_basis` says what a PDF claim's `page` means.

`meta.private: true` stamps "PRIVATE: not for sharing" in every page's footer and on the last page. A `meta.source.licence`
with no Creative Commons deed to link to (for example "All rights reserved") also makes the last page say the paper is not
under an open licence, and prints no "Licence terms" link.

## Composition: scale, cropping and layering

A staged character takes `scale` up to 8, and `x` and `y` may lie beyond the panel (`x` from -0.6 to 1.6, `y` to 3): the panel clips
whatever sticks out, so a large animal can be cropped by the edge, and `y` beyond 1 puts the feet below the panel for a close-up.
To show one organism larger than another, give it a larger `scale` and let it be cropped: a whale at 1.2 to 1.6 (tail cropped at an
edge) beside a krill at 0.8 to 1.0; a krill at 2 to 3 beside diatoms at about 0.4. They are cartoon sizes, not measurements.

Props are drawn first and characters over them, so a character can be placed on or in a prop (a krill inside an `aquarium`).
`front: true` on a prop draws it in front of the characters instead (the glass of a tank, a desk's edge); a prop listed after a
`desk` is also drawn in front, as before. A panel's `device` (`gloss`, `moment`, `close-up`, `aside` or `reveal`) names the kind
of frame it is, so a comic's variety can be asked for and counted (`validate_storyboard.py --variety`).

## Shots: how far away the view is

A panel's `staging` takes `shot: mid | close | wide`. Without it (or with `mid`) every figure is drawn exactly as placed, so a comic
that never sets it renders as before.

| `shot` | What it does | Use it for |
|---|---|---|
| `close` | One figure: the head fills a little over half of the scene's height, low enough to leave room above it for speech, with the neck cropped at the picture's foot (the caption sits under the picture; every picture is cropped there, so nothing runs over it). Two figures: just over two fifths of the height each, side by side. | A reaction, or the payoff. The faces do the work, so pick the expression with care. |
| `wide` | Small figures (scale 0.45), a little above the foot of the panel, with a ground line under them. `ground: false` leaves the line off when a prop is the ground (sea ice, a floor). | An establishing view where the place matters: the gallery room, the ship, the ice. |

The preset fills in only what the author left out: a figure's own `scale`, `x` or `y` always wins. A close-up shows one or two figures;
the validator warns about three or more. The validator's variety check (from 20 panels) also asks for some change of distance, about
one panel in five, and warns if more than two in five are not mid-distance, since a change only lands against a run of mid shots.
The older `close-up` device (a large `scale` and a `y` beyond 1, for an enlargement of an animal or an apparatus) is unchanged.

## Character vocabulary

A staged character takes `pose`, `face` and `facing`; the enums are in the schema and repeated here.

| Field | Values |
|---|---|
| `pose` | `stand`, `point` (front arm out), `hold` (something held out at chest height), `think` (hand to the chin; with something in the hand it becomes `hold`), `shrug` (both hands up and out), `sip` (a hand raised to just in front of the mouth), `up` (both arms raised), `sit` (hips at seat height, thighs forward, hands on the lap; stand the figure at the seat of an `armchair`, `desk` or `piano`) |
| `face` | 22 faces, listed below |
| `facing` | `right` (the default) or `left` |
| `holding` | `marker`, `mug`, `teacup`, `clipboard`, `flask`, `magnifier` |
| `scale` | a multiplier; about 1.0 for people, 1.0 to 1.5 for krill, 0.4 to 0.65 for a whale |
| `body` | overrides the cast member's body, so an `extra` can be an animal: `stick`, `diatom`, `krill`, `penguin`, `whale`, `salp`, `copepod`, `fish`, `worm`, `jellyfish`, `urchin`, `seal`, `seabird`, `moss`, `bacterium`, `seastar`, `dinoflagellate`, `squid`, `amphipod`, `puppet` |


### Faces

A face is two eyes, optional brows and a mouth, plus a mark or two. Pick the one the claim or the line supports; a face is part of what the
panel says (a tearful face on a cited claim that is not about sorrow makes the caption stronger than its claim, as a worried krill would).

| Family | Faces |
|---|---|
| Plain | `neutral`, `deadpan` (flat eyes and mouth), `stare` (wide eyes, pin-prick pupils, flat mouth), `sleepy` (closed eyes, a small open mouth) |
| Pleased | `smile`, `laugh` (eyes shut in a smile, mouth open), `content` (relaxed closed eyes, a gentle smile), `wink` (the closed eye drawn as `<`) |
| Knowing | `smirk` (one corner up, one brow up), `smug` (heavy lids, a smirk), `sceptical` (one brow up, a tilted mouth), `squint` (eyes as chevrons, `> <`), `eyeroll` |
| Troubled | `worry`, `sad` (brows lifted at the middle), `tearful` (glistening eyes, a trembling lip), `plead` (big eyes, brows lifted, a small downturned mouth) |
| Hard | `angry` (brows down and together, mouth pulled down), `determined` (brows set, a firm flat mouth), `disgust` (narrowed eyes, a queasy mouth) |
| Startled | `surprised` (big eyes, brows high, the jaw dropped), `puzzled` (one brow up and one down, a wobbly mouth) |

Four original faces (`neutral`, `smile`, `worry`, `deadpan`) are drawn exactly as before. The rest, `surprised` included, are drawn by
`renderers/xkcd/faces.py` from a table of eye, brow and mouth shapes. Brows are thin lines; hair is drawn small enough, with its fringe high
enough, that a strip of forehead is left for them. Animals draw only the five original faces, `surprised` among them, with their own eyes and mouths; a newer face on an animal uses the nearest of them (`sad` becomes `worry`, `laugh` becomes
`smile`), and a diatom draws all of them. `scripts/asset_gallery.py` shows every face.

**Captions sit under the picture** (the cartoon comes first, and a reader who likes it goes on to the paper's words); speech sits above the head of its speaker inside the picture.

A staging can also be a **split screen**: `split` is a list of exactly two stagings (first, then second) with a frame round each, and `split_labels` prints a few words with them. `split_direction` cuts it `side` (the default: left and right), `stack` (top and bottom) or `slope` (two wedges cut by a slanted line; each half is drawn in the widest rectangle that fits its wedge, so nothing crosses the line). Each half is a full staging with its own characters, props and `shot`. A speech line can point at a figure in either half. **A strip**: `split` may hold three or four stagings with `split_direction: side` (three need a `wide` or `full` panel and share a row only with a `small` one; four need `full`), and a speech line takes `cell` (1 at the left) to say which frame's figure speaks when the same character is in several; the line is wrapped and kept inside its frame, and the panel's caption stays once under the strip. `scripts/asset_gallery.py` shows all three.


A character's look (hair, hair tone, head size, glasses, coat, body) belongs to the cast member in `head.yaml`; see the appearance
options above. Wording a label: use `box` for a multi-word label (it wraps inside its border, grows to hold its words and centres them; there is no signpost: a sign is a `box`).
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
| `paper`, `box`, `label`, `picture` | `label` or `title`; `picture` takes a nested `staging`; `label`'s `x` is its centre and `size` is small, normal or large |
| `arrow` | from `x`, `y` to `x2`, `y2` |
| `sequence` | a strip of DNA letters in four grey tones with one stretch bracketed; `label` names the bracketed stretch (the marker gene) |
| `tree` | a branching tree (a phylogeny); `items`: each `label` names a tip (3 to 9 tips; none gives six unnamed ones) |
| `clusters` | groups of dots on two axes (sequence clusters, an ordination); `items`: each `label` names a group (1 to 4); `label` is an axis note |
| `network` | a small neural network, input on the left; `items`: the first `label` names the input, the last the output; `label` under it |
| `database` | a card-catalogue cabinet with its top drawer open on a row of record cards, each with a strip of DNA-letter cells (a reference library); `label` under it |
| `filter` | a bottle, a filter housing and a pump (filtering water for eDNA); `label` under it |
| `tubes` | a rack of sample tubes (extraction, PCR, stored samples); `label` under it |
| `sequencer` | a benchtop DNA sequencer; `label` under it |
| `cpr` | a towed plankton recorder, generic; `label` under it |
| `echosounder` | a hull, a cone of sound with echo arcs and a few dots; `label` under it |
| `ctd` | a CTD rosette: a ring of sampling bottles round a frame, the sensor package low in the middle, a lifting bail; `label` under it |
| `net` | a plankton net hung to be hauled up: bridle, ring, cone of mesh, collecting bottle; `label` under it |
| `bongo`, `trawl`, `rmt` | towed nets: a bongo net (two rings and cones, a weight), a midwater trawl (doors, floats, weights, funnel, cod end), a rectangular midwater trawl (two frames with nets and a depressor); `label` under each |
| `map` | a round map of the south polar region with the real coastline (Natural Earth, public domain, simplified): `view: polar` (default; Antarctica, to 50 degrees S) or `view: wide` (to 10 degrees S, adding Australia, Tasmania, New Zealand, southern Africa and South America); `places`: each `lon`, `lat` (south and west negative) and `label`; `label` under it |
| `currents` | the major currents as arrows, for laying over a `map` with the same box and `view`: the Antarctic Circumpolar Current, the Weddell and Ross gyres, and in `wide` also the East Australian, Leeuwin, Agulhas and Humboldt currents |
| `stake` | a mass-balance (ablation) stake: a banded pole with tick marks and a flag, set in a melt hollow in the ice; `label` under it |
| `emsled` | an ice-thickness sensor on a sled: the sled, a long electromagnetic boom with a coil box at each end, a GPS antenna, a tow rope and signal arcs going down into the ice; `label` under it |
| `fieldcamp` | a polar field camp: a tent with guy lines, a loaded cargo sled and a flag on the ice; `label` under it |
| `molecule` | a generic ball-and-stick molecule (a six-ring with a double bond and a zigzag tail); decoration, not a particular compound; `label` under it |
| `iceberg` | a tabular iceberg: a flat-topped block with weathered sides, its much larger submerged part pale and dashed below the waterline; `label` under it |
| `iceshelf` | an ice shelf in side view: a slab with a cliff, strata, a crack, the floating part below the water and a calved berg; `label` under it |
| `seaice` | sea ice from above; `condition`: `pancake` (small round rimmed floes), `pack` (angular floes tightly packed), `drift` (a few floes, open water between) or `fast` (a cracked sheet against the coast); `label` under it |
| `mixedlayer` | a section of the upper ocean: wind, a mixed surface layer with eddies, a thermocline of packed lines and still deep water; `items`: up to three `label`s, top to bottom, set at the right |
| `satellite` | a satellite with solar panels and a cone down to a footprint (remote sensing); `label` under it |
| `radar` | a radar or lidar dish on a mast with signal arcs; `label` under it |
| `icecore` | one regular cylinder with straight sides, a flat top, two cuts across it and faint layer lines; `label` under it |
| `massspec` | a mass spectrometer or chromatograph with a column and a screen of peaks; `label` under it |
| `helicopter`, `drone` | the vehicle; `label` under it |
| `aquarium` | a tank with water, bubbles and gravel; `label` under it |
| `freezer` | an upright freezer with a snowflake; `label` under it |
| `clay` | a lump of clay with thumbprints, pinched balls and a slab cut into squares; `label` under it |
| `mosaic` | a framed mosaic of tiles with a few places still empty; `label` under it |
| `tag` | an animal satellite tag: a streamlined case on a base plate, a strip of solar cells on top, a whip antenna with signal arcs; `label` under it |
| `scatter` | dots round a dashed fitted line on two axes; `x_label`, `y_label` name the axes |
| `boxplot` | box-and-whisker plots for two to four groups; `items`: each `label` names a group |
| `modelgrid` | a globe and a patch of it cut into grid cells (a numerical model); `label` under it |
| `venn` | two overlapping circles; `items`: the two circles' `label`s; `label` names the overlap |
| `stage` | a theatre stage seen from the front: curtains, a valance and boards; `spotlight` (a cone of light on a dark back), `screen` (a screen at the back), `audience` (a row of heads in front); figures and puppets stand on the boards |
| `blackbox` | a black box with a question mark, an arrow in and an arrow out; `items` label the input and output; `dashed` draws the output dashed (an effect not shown) |
| `circle` | chairs round a centre, seen from above and in front; `chairs` (3 to 8), `centre`: `fire`, `easel` or `person` |
| `bridge` | a bridge between two blocks; `items` label the blocks; `broken` leaves a gap in the deck |
| `eye` | an eye; `lens` puts a lens in front, `thought` a thought bubble (a string puts words in it) |
| `bookshelf` | two shelves of books; `gap` leaves a slot about two books wide empty (dashed, with a question mark) |
| `spinalcord` | a schematic cross-section: white matter, grey horns, central canal; `laminae` dashes layers across a dorsal horn, `hemisection` darkens one half |
| `brain` | a side-view brain (front at the left) with a frontal, temporal, parietal and occipital lobe, the lateral fissure and central sulcus, folds, a ridged cerebellum and the stem; `highlight` (a lobe, or `left` or `right`), `labels` (name the lobes), `tracts` (fibre bundles), `signal` (an arrowed route); `view: top` or `highlight: left`/`right` draws it from above as two hemispheres |
| `gallery`, `book`, `brain` | options for missing things: `gallery` `empty: n` (the last n frames dashed with a question mark), `book` `blank` (a dashed silhouette on the cover), `brain` `signal` (one arrowed route) |
| `desk`, `ship`, `bowl`, `bottle`, `jar`, `flash`, `cups`, `laptop`, `microscope`, `teapot`, `thermometer` | objects; `label` where one is shown; `cups` takes `items` with a `value` (how full). `laptop`, `microscope`, `teapot`, `net` and `thermometer` keep their proportions inside the box you give them |

**The schematic props** (`sequence` to `mixedlayer`, above) are generic pictures of common equipment and analysis steps. Their
shape, count and size mean nothing: the dots in `clusters`, the letters in `sequence`, the nodes in `network`, the tips
of an unnamed `tree` and the dots in `echosounder` are decoration. The footer of every comic says the pictures are cartoon stand-ins, so do not label a panel "schematic" (the validator warns); put every
claim in the caption, and never read a number or a result off one. A `map`'s coastlines are real but simplified, and a pinned `place` states a location: only pin a place that a cited claim names, and take its coordinates from a reference, not from memory. None of them draws a number, so they never need a claim
by themselves; a `label` you add that contains a number does.

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
