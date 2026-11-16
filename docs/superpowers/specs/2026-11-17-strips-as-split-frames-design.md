# A multi-frame gag as a split frame

Status: built 2026-11-17 (decisions below). The review page's change-the-picture block lists a panel's top-level characters and props, so a strip's own frames are edited in the beat file for now.

## The problem

A joke often needs three frames to set up (xkcd 927: the situation, a character's plan, the twist). The pipeline has no way to say
"these frames belong together". Trying it with three ordinary panels (B4.2 to B4.4 of the eDNA comic, 2026-11-17) went wrong:

- the layout packs rows by weight, so the strip fell as two frames plus one, and the punchline frame was cramped;
- the paper's caption had to squeeze into a third-width frame;
- panel ids are `B<n>.<m>`, so adding two frames meant renumbering nine panels across five files.

## The idea

The split frame already does most of this: one panel, a `split` of stagings drawn side by side with a frame round each, `split_labels`
above them, `split_direction` (side, stack, slope), speech that can point at a figure in any half. A strip is a split with more than two cells.
Because it is **one panel**, the layout, the ids, the claims and the humour note all stay as they are, and the panel's caption stays once,
under the strip (captions sit under the picture in every panel, so a reader who likes the cartoon goes on to the fact).

## Changes

1. **Schema.** `split` takes 2 to 4 stagings for `side` and `stack`; `slope` stays at exactly 2. `split_labels` takes up to 4.
   A speech line gets an optional `cell` (1-based) naming which frame's figure speaks. Without it, a line points at the speaker's
   first appearance, exactly as now.
2. **Renderer.** `split_cells` returns N cells for `side` (columns) and `stack` (rows). `stage()` records each head under `id` and under
   `id@n`; `speech_layout`, `plan_panel` and `speech_obstacles` look up `id@n` when a line has `cell`. Nothing else changes: a
   two-cell split, and every panel that has no split, draws exactly as before.
3. **Validator.** `cell` must be within the split's cell count, and its speaker must be staged in that cell. A strip of three or more cells
   on a `small` or `standard` panel gets a warning (it will be narrow): the fix is `weight: wide` or `full`.
4. **Review page.** No new code: a joke panel is shown as drawn, and a strip is one panel. (A second copy with the captions covered was tried
   and dropped: the reader can judge the sixth question from the one picture.)
5. **Docs and gallery.** `renderers/README.md`, the storyboard skill and the humour-pass skill say when to use a strip; the asset gallery
   and the review sheet each get a three-cell example.

## Not doing

- Per-frame captions (a caption stays at panel level).
- Different frame widths or a mix of directions inside one strip.
- Auto-converting existing comics.

## Safety

The layout and the 15 existing comics must not change. Before and after, hash every panel's SVG across all comics (the method used for
the speech-placement fix) and require zero differences. Tests: a three-cell side strip and a three-cell stack, a speech line with
`cell` picking the right one of two identical characters, the validator's two new checks, and the existing two-cell tests unchanged.

## Then the eDNA comic

Undo the renumbering (B4.3 to B4.13 return to their old numbers), and write the joke as one `B4.2` of `weight: full` with a three-cell
`side` split: the paper's caption under the strip; frame 1 Ines "Ten labs, ten protocols." with the sequencer and tubes; frame 2 Otto "Ten protocols?
Ridiculous. We need one that covers everybody."; frame 3, labelled "soon", the board of "the ten" and "Otto's" and Ines "That's eleven."
The `humour` block stays on B4.2 with the six questions answered.

## Decided

1. Up to 4 cells; **four need a page-wide (`full`) frame**, three need `wide` or `full` and share a row only with one `small` panel. The layout enforces
   it (a strip is never given less) and the validator makes a narrower weight an error.
2. The speech field is `cell`.
3. Strips are `split_direction: side` only; `stack` and `slope` stay at two cells.
