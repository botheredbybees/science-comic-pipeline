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
5. **Render.** One renderer per style, reading only the storyboard.
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

## Licensing policy

- Code and schema: MIT. Examples, docs and rendered output: CC BY 4.0.
- Source papers are never copied into the repo. Only CC BY or CC0 papers are used as
  examples, and each records where and when the licence was checked (Europe PMC's
  `license` field is a good source for anything in PMC).
- A NoDerivatives licence (CC BY-NC-ND, or older Journal of Science Communication
  articles) rules a paper out as an adaptation source.
- Nothing from any employer's internal systems, data or credentials goes in this repo.

## Not decided yet

- Which model-independent form the skills take (plain Markdown prompts, plus a CLI?).
- Whether the `painted` renderer is worth building, or needs an image model.
- How to check a joke automatically, if at all.
- Page format for output (SVG per page, PDF, or both).

## Next steps

1. Check the example's claims against the full text and mark them `verified` or fix them.
2. Build the `xkcd` renderer against the schema.
3. Write the `source-to-claims` and `story-spine` skills from what that example needed.
4. Compare the xkcd output with the hand-painted version of the first comic.
