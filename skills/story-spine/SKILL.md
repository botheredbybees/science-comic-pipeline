---
name: story-spine
description: Use after the claims ledger exists and before drafting panels. Finds the story in a paper (And / But / Therefore), picks the cast and audience, says what is left out, and plans the beats and which claims each one carries.
---

# Story spine

**Goal:** decide what the comic is about before drawing a panel. Papers describe outcomes; a comic needs
a situation, a complication and a consequence. This step finds them in the paper's own words and
writes down the plan: `head.yaml` and a beat plan.

**You need:** the finished `claims.yaml` (see `source-to-claims`). Work from the claims, not from memory
of the paper, and plan with claim ids.

## 1. Pick the audience

Write one sentence in `meta.audience`: who reads this and what they already know. "Marine science students"
and "anyone who has wondered which plankton move carbon out of the surface ocean" give different comics.
A general reader needs a term explained once, in a caption, the first time it appears.

## 2. Find And / But / Therefore

The spine is three sentences in `meta.spine`, each drawn from claims:

- **And:** the ordinary world. What is known or assumed (background claims).
- **But:** the complication. The gap, the problem, the surprise. Look in the paper's last Introduction
  paragraph ("however", "little is known", "it remains unclear") and in any result that went against the
  assumption.
- **Therefore:** what the authors did and what followed (method and result claims).

(From Randy Olson's narrative template. IMRaD already maps onto it: Introduction is the ordinary world and
the problem, Methods are the tools, Results are the ordeals, Discussion is the return with something useful.)

**When the paper has little conflict**, look for tension that is really there: a negative result ("the most
abundant organism explained none of it"), a method that nearly failed, a result that contradicts the textbook,
a caveat the authors stress. Do not invent a villain, a controversy or a stake the paper does not have.
If the honest story is "we measured it and here is what it looks like", say so and let the cast and the
visuals do the work.

## 3. Choose the cast

- Usually one **guide**, a person in the paper's world (a scientist on the ship, a student), who asks the
  reader's questions. Give them a simple look (`appearance`: `hair` is one of none, bob, long, ponytail, bun, spiky, beanie, hardhat; `hair_tone` is dark (the default, solid black), light (an outline only) or strands (curved strokes; both are blond; not for spiky); `glasses` and `coat` (a lab coat) are true or false, and `outfit` (floatcoat, parka or hivis) replaces the lab coat for work on a ship's deck or the ice: dress a character for where they are standing; `body` is stick by default).
- Organisms or things that carry the result can be characters (`body: diatom | krill | penguin | whale | salp | copepod | fish | worm | jellyfish | urchin | seal | seabird | moss | bacterium | seastar | dinoflagellate | squid | amphipod`
  are drawn, from copepod on as generic cartoon shapes; other things are props or `extra`). A walk-on animal that is not a recurring character needs no cast
  entry: stage `{ id: extra, body: penguin }`. If your organism has no body, use a stick figure and caption what it is
  (and say so in the cast `role`); do not draw a body the renderer cannot. Other organisms (a bivalve, a sponge) have no body:
use a labelled stick figure. A walk-on that must speak needs a cast entry. A character must not be made to say something the
  organism did not do: playing "Dot, the diatom" is fine; giving it motives the paper does not report is not.
- **The picture is the subject, not the cast.** Plan the story so that most beats can show organisms, apparatus, data or
  a diagram; the guide asks and points, and is not in every panel. A beat whose only possible picture is two people
  talking should be folded into its neighbour.
- Fewer is better. Three or four recurring characters; others are `extra` (with a `body` when they are animals).

**The honest tension may be in the method, not the result.** A methods or intercalibration paper's headline ("the labs
agree") can depend on a step the authors took themselves (samples removed as contaminated, "based on taxonomic
composition"). Put that basis in the next panel after the payoff, and let a character ask the reader's question.
**When the brief names a concept the paper does not** (eDNA, metabarcoding, a model), do not use the word; say so in
`left_out` and `PLAN.md`.

**Jargon.** A general reader needs terms explained, but the comic may add nothing the paper does not say. Use
the paper's own gloss ("a parasitic dinoflagellate group"), which you put in the ledger as a definition claim. If the
paper gives none, keep the term and list it in `left_out`, or leave it out; do not write a definition from memory.

## 4. Say what is left out

`meta.left_out` is required in practice: a list of what the comic skips and why (statistics, protocols,
supplementary tables, caveats you could not fit). A condensed comic is honest when it says it condenses.

## 5. Plan the beats

A beat is a short sequence of panels with one job. Typical: *problem*, *method*, *suspects / results*,
*why it matters*, *what next and the caveats*. There is **no limit on panel count**: a plan of five to eight
beats is normal; panels per beat follow the material. For each beat write:

| beat | job | claim ids | the weight and rhythm it needs |
|---|---|---|---|

Use McCloud's ideas (*Understanding Comics*, *Making Comics*) to pace it: a wide quiet panel is a pause; a
small panel a quick beat. Mark where the reader needs a breather, where a chart is the point, where the
payoff lands, and where the caveats go (they belong in the comic, near the claim they qualify).

A rule of thumb: about one claim per panel, so a paper with 60 usable claims makes a comic of 30 to 50 panels; a
perspective piece with fewer facts makes a shorter one. A claim-dense primary paper (100 or more claims) makes 70 to
85 panels on 13 to 15 pages: that is acceptable, but group two related claims in one panel before you add a page, and
keep a method paper to what its story needs. Claim ids may appear in `meta.spine` text, as in the examples.

Every claim you plan to use must exist in the ledger. If the story needs a statement that is not in it, go
back and add it (with a quote), do not write it into a panel.

## When the comic covers several papers (a topic comic)

Decide this in step 1 of the pipeline, before the claims (`HOWTO.md`, "One paper, or several?"). A topic comic answers one question
from two to six papers. Its spine is about the question, not any one paper:

- **And:** what the papers take as the ordinary world (background claims, from any of them).
- **But:** what the papers' evidence cannot settle: a measure that showed little, a method that was hard to apply, studies too small or
  too thinly described. Take it from the papers' own caveats; do not invent a controversy. Where two papers pull in different directions,
  that is the tension: put both claims side by side and do not decide between them unless a paper does.
- **Therefore:** what the papers say follows, and what they say is still needed.

Rules: name the paper in a caption whenever the claim is one paper's finding; never credit one paper with another's result; do not rank
the studies unless a source does, and list in `meta.left_out` that they differ in design and size; and **end on the topic's open
question**, taken from what the papers themselves call for (the claims where the authors say further research is needed), cited.
Plan the beats by theme (what they set out to do, what they found, what is hard to measure, what is open), not paper by paper.
Give each claim id in the spine a paper, since a reader of `PLAN.md` will want to know whose it is.

## head.yaml skeleton

```yaml
version: 2
meta:
  title: "A short title"
  audience: "One sentence"
  left_out: ["What the comic skips, and why"]
  source:
    title: "..."          # from sources/<slug>/source.json
    authors: ["A B", "C D"]
    year: 2022            # an integer, not a string
    doi: "10.xxxx/xxxx"
    url: "https://doi.org/10.xxxx/xxxx"
    licence: "CC BY 4.0"
    licence_checked: "Europe PMC full-text XML, 2026-11-13"
  spine: { and: "...", but: "...", therefore: "..." }
cast:
  - { id: ines, name: "Ines", role: "A scientist on the ship", look: "Stick figure in a woolly hat", appearance: { hair: beanie } }
```

For a topic comic, replace `meta.source` with a list, and give every claim a `source.ref` naming one entry:

```yaml
meta:
  title: "..."
  audience: "..."
  private: true            # when any paper is not open access
  sources:
    - { id: smith-2020, title: "...", authors: ["A Smith"], year: 2020, doi: "10.xxxx/xxxx", licence: "CC BY 4.0",
        licence_checked: "where you read it, date", page_basis: "PDF page index, 1 to 12" }
    - { id: jones-2019, title: "...", authors: ["B Jones", "C Lee"], year: 2019, licence: "All rights reserved (Publisher)",
        licence_checked: "where you read it, date", page_basis: "PDF page index, 1 to 9" }
  spine: { and: "...", but: "...", therefore: "..." }
```

## Output

- `examples/<slug>/head.yaml`: `meta` (title, audience, source, spine, left_out) and `cast`.
- `examples/<slug>/PLAN.md`: the audience, the spine and the beat table: one row per beat with its id, title, job
  (problem, method, result or discussion), the claim ids it carries, and the rhythm it needs (where the pause, the
  chart and the payoff fall). A page of notes, not a form: the storyboard is the product.

**Done when:** the spine uses only claims from the ledger, the audience and the left-out list are written,
and every beat has a job and claim ids.
