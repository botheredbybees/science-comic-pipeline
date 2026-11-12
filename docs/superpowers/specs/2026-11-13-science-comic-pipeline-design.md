# Science comic pipeline: design

Date: 2026-11-13. Status: draft, written at project start from the decisions below.

## Goal

A repeatable, publicly usable process that turns a scientific paper into a short comic
without losing what the paper says. Making papers and data products accessible matters as
much as producing them. The tool should work for any field and any capable model.

## What the first attempt taught us

A first comic, an explainer for a long instrument guide, was built by hand as one SVG per
page. It took many iterations, and the problems were structural:

- Content (what the panels say) and rendering (how they look) lived in the same files, so
  changing the style meant redoing the content.
- Accuracy was kept in the author's head. Nothing recorded which sentence in the comic came
  from which place in the source.
- Hand-written vector art kept reading as flat and repetitive. Characters shared one kit
  and one set of expressions.

So: separate the storyboard from the renderers, and make accuracy something a script checks.

## Pipeline

1. **Source to claims.** List what the paper claims. Each claim has a locator (section,
   page, table, or `abstract`), a `kind`, and a `status`. `verified` means checked against
   the full text; `abstract_only` and `unverified` are drawn only with a warning.
2. **Story spine.** Reduce the paper to And / But / Therefore (Randy Olson's narrative
   template; the citation is to be added after it is checked). IMRaD already maps onto a
   journey: Introduction is the ordinary world and the problem, Methods are the tools and
   the road, Results are the ordeals, Discussion is the return with something useful.
3. **Storyboard.** Pages of panels with scene, speech and the claims each panel relies on.
   Validated by `scripts/validate_storyboard.py`.
4. **Humour pass.** Jokes are drafted separately, attached to panels as a `humour` block,
   and flagged. If a joke would change a claim, the claim wins.
5. **Stage and render.** A sentence cannot be drawn by a program, so each panel can carry a
   `staging` block (characters, poses, props). The agent writes it as the "artist" step; one renderer
   per style draws it, reading only the storyboard.
6. **Visual QA.** Render, screenshot, and check for overflow, overlaps and unreadable text.

## Accuracy rules (enforced by the validator)

- Speakers must be in the cast or `narrator`.
- A panel citing a claim id that does not exist is an error.
- A panel whose dialogue contains a digit but cites no claim is an error.
- A claim not `verified` but drawn in a panel is a warning, with its `note` shown.
- A claim in the ledger that no panel uses is a warning.
- A joke on a panel that cites claims is a warning until a reviewer sets `keeps_claims_intact`.

The check on numbers is deliberately blunt. Number words ("seventy-nine") are not caught.

## First style to build: xkcd-like

xkcd is a source of ideas for the look, not of content or artwork. Traits to reproduce:

- Some panels are outlined and some are borderless.
- Straight lines and curves carry a hand-drawn wobble.
- Speech has no balloon: a short line joins the text to the speaker.
- Stick figures, almost no colour, text in a handwriting-like face whose licence must be
  checked before it is bundled.
- Charts and diagrams are first-class panels, not decoration.

Matplotlib's `plt.xkcd()` is the obvious starting point for the wobble. It imitates the
style and does not reuse xkcd artwork.

## The hard parts

- **Humour.** Dry humour can be partly systematic (deadpan understatement, an earnest
  caption against an absurd image, a running gag, the authors' own caveats played straight)
  but it needs a human edit. The pipeline drafts jokes as optional and flagged.
- **Story from IMRaD.** Papers are written as descriptions of outcomes, not as stories.
  The spine step has to find the conflict, and sometimes a paper has little. The first
  example (a study whose headline is that a difference exists) is a test of that.

## Layout and delivery (decided 2026-11-13)

- **No limit or guideline on panel count.** A comic has as many panels as the story needs.
  xkcd's short strips inform the look, not the length.
- **The sideways strip is the primary reading flow on the web.** It suits a story that moves
  through time. It needs visible arrows, keyboard support, a progress cue, and a vertical
  fallback on phones, because mouse wheels scroll vertically.
- **PDF reads like a printed comic:** left to right across the page, then down.
- **Panels vary in size**, as in printed comics. Size and shape carry time and emphasis: a wide,
  quiet panel reads as a pause, which is also a timing tool for deadpan humour.
- **The storyboard holds no pages.** It is an ordered sequence of beats of panels. A separate
  layout step decides how they flow (one strip, or rows packed to the page width), so one
  storyboard serves the web, a PDF and slides.
- **Reference:** Scott McCloud, *Understanding Comics* (1993) and *Making Comics* (2006).
  Ideas to use, from memory and still to be checked against the books: the six panel-to-panel
  transitions (moment-to-moment, action-to-action, subject-to-subject, scene-to-scene,
  aspect-to-aspect, non-sequitur); the modes of word and picture combination; and the five
  choices (moment, frame, image, word, flow) as the per-panel checklist. Implemented per-panel
  fields (schema version 2): `weight` (small, standard, wide, full: a third, a half, two thirds or all
  of a row, as a preference), `transition` (not allowed on the first panel) and `word_picture`.

## Row packing (decided 2026-11-13)

- Printed rows are the most effective view, so the PDF and the print layout use them.
- **No blanks.** Every row is filled exactly; a gap is never an acceptable way to absorb a mismatch.
- **At most 3 panels across by default** (a parameter; 4 suits a wider page). On A4 portrait that
  leaves about 63 mm for the narrowest panel (a third of the row), enough for a caption. The
  figures for real comics (Western pages mostly 1 to 3 across, about three tiers; Franco-Belgian
  albums 2 to 4 across; manga 1 to 3) are from general knowledge, not measured.
- **The packer looks ahead.** `scripts/layout.py` finds the row breaks and widths for a whole beat
  that keep every panel closest to its preferred width (least squares, like line-breaking in
  typesetting). A standard and a wide panel in one row become 5/12 and 7/12. A `full` panel is
  always alone.

## xkcd renderer (built 2026-11-13)

`renderers/xkcd/render.py` draws stick figures with seeded, jittered geometry (not an SVG filter, so
PDF converters keep it), outlined and borderless panels, speech joined to the speaker by a line,
and a small prop library (boards, slides, bar charts, papers, a phone, a bowl, a wall, signs, nested
pictures, a desk). The example renders as 2 A4 pages. Pagination tries panels at several heights and
keeps the tallest setting that needs the fewest pages, so a last page is not left nearly empty. The
attribution a CC BY source requires is printed on the last page from `meta.source`.

Open points: text is wrapped by an average glyph width, not measured; figures stay small in wide,
short panels; the staging vocabulary is small and fixed, with `box` as the fallback.

## Verifying claims against the source (built 2026-11-13)

A claim may only be `verified` if it carries a `quote` and a `page`, and `scripts/check_quotes.py`
finds the quote on that page of the source text (case, punctuation, line breaks, hyphenation and
ligatures ignored). It also warns when a number in the claim is not in its quote. This is the
machine half of verification; whether a claim says only what its quote supports is still a human
or model judgement.

First long run (a 160-page user guide): three fresh agents, one third of an existing comic each,
wrote 242 claims with quotes and a list of problems in the existing comic. The checker found 0 errors
in their files, and 9 claims they could not support were left `unverified` and kept out of the panels.
Lessons: run the checker yourself and read the files, because an agent's summary got two claim ids
swapped; the agents flagged about 90 statements in the earlier comic that overstated, dropped a hedge
from, or mis-cited the guide, so a comic made without this step is likely to carry errors a reader
would repeat.

## Row heights (built 2026-11-13)

Rows were all as tall as their tallest panel, which left whitespace at the bottom of most pages and made
every row look alike. After pagination the renderer now shares each page's spare height among its rows
unevenly: by how much is in them (charts, a full-width panel, props), by an optional per-panel `height`
hint (`short`, `standard`, `tall`), and within limits (a row may grow by about half, a plain row may
shrink a little unless its speech needs the headroom). A sparse last page is not stretched. This also
uses panel height as emphasis, as McCloud describes.

Two readability rules came from reading the output: neighbouring rows should not have the same widths
(the packer penalises a repeat, more for identical widths than near-identical ones, and the penalty is
tuned so the page count does not grow), and two rows of only open panels must not be adjacent (the
renderer outlines the widest panel of the second). Chart labels are never truncated; if they do not fit,
the overflow check shows it.

## Licensing policy

- Code and schema: MIT. Docs: CC BY 4.0. Rendered output carries the licence of its source: an
  adaptation of a CC BY paper is CC BY; an adaptation of a CC BY-SA paper must be CC BY-SA (ShareAlike).
  A source with no stated licence is not used until it is confirmed.
- Source papers are never copied into the repo. Only CC BY, CC BY-SA or CC0 papers are used as
  examples (with ShareAlike carried through), and each records where and when the licence was checked (Europe PMC's
  `license` field is a good source for anything in PMC).
- A NoDerivatives licence (CC BY-NC-ND, or older Journal of Science Communication
  articles) rules a paper out as an adaptation source.
- Nothing from any employer's internal systems, data or credentials goes in this repo.

## Not decided yet

- Which model-independent form the skills take (plain Markdown prompts, plus a CLI?).
- Whether the `painted` renderer is worth building, or needs an image model.
- How to check a joke automatically, if at all.
- Output formats beyond the strip and the PDF (slides, per-panel images).
- Whether packing should run across beat boundaries. Today each beat starts a new row, so a beat
  that ends on an odd panel leaves one panel alone at full width.

## Next steps

1. Check the example's claims against the full text and mark them `verified` or fix them.
2. Build the `xkcd` renderer against the schema.
3. Write the `source-to-claims` and `story-spine` skills from what that example needed.
4. Compare the xkcd output with the hand-painted version of the first comic.
