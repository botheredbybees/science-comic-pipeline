---
name: storyboard
description: Use after the claims ledger and the story spine exist. Writes the beats and panels (scene, speech, staging) so that every fact in a panel cites a claim, then assembles and validates the storyboard and previews it.
---

# Storyboard

**Goal:** turn the plan into `beats/B*.yaml`, a storyboard that the validator accepts with no warnings and a
renderer can draw. You are writer and artist: the renderer draws only what you stage.

**You need:** `claims.yaml`, `head.yaml` and `PLAN.md` from the earlier steps, and
[`renderers/README.md`](../../renderers/README.md) for the staging vocabulary (characters, poses, faces,
props, charts).

## The working folder

```
examples/<slug>/
  head.yaml          meta + cast
  claims.yaml        the ledger
  beats/B01-name.yaml a YAML list of beats; each beat has id, title, act, panels
```

Beat files are read in numeric order (B2 before B10), so zero-padding is not needed, but it keeps `ls` tidy.
**Quote every caption, line and scene in YAML** (a colon or a comma inside an unquoted string breaks the file, and the
error that comes back is a misleading schema message, not a YAML one). Panel ids only have to be unique.

`act` is one of `problem`, `method`, `result`, `discussion`. Panel ids are `B<beat>.<n>`.

## A panel

```yaml
- id: B3.1
  weight: standard            # small | standard | wide | full  (a third, half, two thirds, all of a row)
  frame: outlined             # or borderless
  height: standard            # short | standard | tall (optional hint)
  transition: scene-to-scene  # how it follows the last panel; none on the first panel of the comic
  word_picture: parallel      # optional
  scene: "What the reader sees, in a sentence (also the alt text)."
  speech:
    - { speaker: narrator, kind: caption, text: "Diatoms dominated the community, an average of 41% of all reads." }
    - { speaker: dot, text: "Forty-one percent. Take note." }
  claim_ids: [C20]
  staging:
    characters: [ { id: dot, x: 0.8, pose: up, face: smile, facing: left, scale: 0.85 } ]
    props: [ { kind: bars, x: 0.08, y: 0.04, w: 0.5, h: 0.9, max: 100, unit: "%", bars: [{ label: diatoms, value: 41 }] } ]
```

## Rules the validator enforces (run it, read what it says)

- **Every fact cites a claim.** A panel whose text or chart contains a number must cite a claim whose text
  or quote contains that number. Cite every claim a panel relies on, nothing it does not.
- Captions carry the claim. **Keep the hedge, the direction and the scope** of the claim's wording; a
  caption may shorten a claim, never strengthen it.
- Speakers are in the cast or `narrator`; staged characters are in the cast or `extra`. A walk-on that speaks needs
  a cast entry: the staged `extra` cannot be a speaker.
- Use only `verified` claims. An `abstract_only` or `unverified` claim draws a warning; fix it, or leave it out.
- `build_storyboard.py` lists the verified ledger claims that no panel cites. That is a prompt, not an error:
  check that none is a claim you forgot, and leave the rest. (The built storyboard keeps only cited claims, so the
  validator cannot see the others.) Do not delete claims from the ledger to silence it.
- A joke on a panel that cites claims draws a warning until a reviewer sets `keeps_claims_intact: true`
  (see `humour-pass`). That warning is deliberate: it is how a joke waits for a human.

## Writing well

- **One idea per panel.** Say it in a caption of about 12 to 35 words, plus at most a line or two of
  dialogue. A caption that needs four sentences is two panels.
- A guide asks the question the reader would ask; a character may react; nobody lectures.
- Vary the rhythm, as in a printed comic: a `wide` quiet panel is a pause, a `small` one a quick beat,
  a `full` panel the payoff. Use `transition` and `word_picture` honestly (McCloud): they are notes about
  the reading, and the first panel has no transition.
- Mix `frame`: some outlined, some borderless. (The renderer outlines a panel itself when two rows of only open panels would run together.)
- Put a chart where the data is the point. Draw it honestly:
  - never draw a value that is not in a cited claim; a schematic line is dashed or dotted and its panel says "schematic" or shows only the
    claim's own numbers;
  - set `max` only when it is in a claim (percent charts may use 100); use `show_max: false` to hide an axis maximum you cannot cite;
  - a chart with several bars is better in a `full` panel: `weight` is only a preference, so a `wide` panel can be packed at a
    third of a row and the chart will collide (the field names every prop reads are in `renderers/README.md`);
  - `bars` draws its `title` above the chart and stands bars on a zero line, so a signed index (Ivlev's, -1 to +1)
    is `min: -1, max: 1` with negative bars hanging down. Each chart is scaled to its own tallest bar unless you
    give `max`, so heights do not compare between panels: give related charts the same `max`, or say so in the caption;
  - tick numbers on an `axis` and a shown `min` or `max` count as numbers: cite the claim that defines the scale;
  - `height: tall` helps people and bar charts, not a thin `axis` (it only adds empty space above it).
- Stage everything the picture needs: where each character stands (`x`, `scale`), who faces whom, and the
  props. Leave room above speakers for their text. Krill are small: give them `scale` 1.3 to 1.5 alone, 1.0 to 1.2 beside other figures
  (at 1.4 one is a third of a panel's width). A salp is about as wide as a person is tall; a whale needs 0.4 to 0.65.
- **The `scene` text is the panel's alt text: describe only what is staged.** The validator warns when
  a scene names a prop (ship, bowl, bottle, jar, desk, phone, slide, pie, board, teapot, laptop, microscope, thermometer) that is not staged, but it cannot see
  anything else, so a scene that mentions a calendar or an ocean that is not drawn is a defect you must catch. It
  also warns when a scene names an object (mug, notebook, clipboard, flask, magnifier) that nobody in the staging holds. A character holds
  only a `marker`, `mug`, `teacup`, `paper`, `clipboard`, `notebook`, `flask` or `magnifier` (vary them: one object for a
  whole comic goes stale); the room's props are in `renderers/README.md`; stage anything else as a prop.
- **Shortening a long claim.** A caption is 12 to 35 words, and some claims are longer. Cut examples, asides and
  the second of two parallel facts, and keep, whole, anything that carries a hedge ("may", "suggests"), a number with
  its unit, or a scope ("in this region"). If the hedge sits in the middle of the sentence, keep the middle: split the
  claim across two panels rather than trim it.
- **Number words are mostly not checked.** The validator knows one to ten and cannot tell what they count (a "four"
  in a claim about four swarms also "supports" "four males"), and it does not know "fifteen hundred". Check number
  words against the claims yourself. A bar whose value comes from a number word needs the digit in a claim
  too, or leave the value off. Thousands separators ("55,465", or the PDF's "55, 465") are matched as one number.
- **Text on props.** Use `box` for any label longer than a few words: it wraps. `label` does not wrap and is cut off
  at the panel's edge; `board` shrinks its cards to fit, so more than three cards, or a clause on a card, becomes
  unreadable (the validator warns). `steps` labels wrap, but keep them short. A `stack` or `bars` with equal items
  says "so many equal parts": the number of segments is itself a claim (five 20s need "100 in 20 mm sections").
- **When only part of a ranking is verified**, do not draw it with `steps` or `axis` positions, which imply the whole order;
  use two `box` props or a two-tier layout.
- **A crowd.** Four krill at scale 1.0 touch in a standard panel (a krill is about 60 units wide at 1.0, so at most two);
  for "ten groups" a row of identical `extra` figures works. A lone small figure in a tall row looks tiny: give it `scale`
  1.0 to 1.5, and `weight: wide` with `scale` beats a wide panel packed beside a three-line caption.
- **Stand-ins.** The renderer draws diatom, krill, penguin, whale and salp. A copepod, fish, worm or urchin is a labelled
  stick figure (an `extra` with a label, or a cast entry that says so); do not caption a plain figure as if it were drawn
  as the animal.
- Do not invent facts in `scene`, in props, or in a character's face: a worried krill implies the paper
  says krill are at risk, so only draw it if a cited claim does.

## Build, validate, look

```bash
python scripts/build_storyboard.py examples/<slug>                       # writes storyboard.yaml, keeps cited claims
python scripts/validate_storyboard.py examples/<slug>/storyboard.yaml --strict
python scripts/check_quotes.py examples/<slug>/claims.yaml --pages-dir sources/<slug>/pages --strict
python scripts/preview_storyboard.py examples/<slug>/storyboard.yaml -o output/<slug>-preview.html   # a readable page to review the story
```

Fix every error and warning before the next step. Reading the preview as a stranger would, ask: does the
story make sense without the paper? Is any caption stronger than its claim?

**Done when:** `check_quotes.py --strict` is clean and `validate_storyboard.py --strict` has no errors and
no warnings except one per joke still awaiting a human. Then run
`humour-pass` (optional) and `visual-qa`.
