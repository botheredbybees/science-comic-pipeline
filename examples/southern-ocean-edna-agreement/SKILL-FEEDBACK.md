# Skill and pipeline feedback from the topic comic "Does eDNA agree with itself?"

Found while following the five skills cold on three papers (2026-11-16). Nothing in `scripts/`, `renderers/`, `schema/`, `skills/` or `tests/` was changed by the build.

**Status, 2026-11-16 (fixed afterwards, with tests):** fault 1 (`check_quotes.py --pages-root` now reads the papers from `meta.sources` or, for a bare `claims.yaml`, from the `source.ref` of its claims, and says plainly when it has neither); fault 2 (the validator now looks inside `split` halves for staged props, labels and words, and counts `split_labels` as words); fault 5 (a `bars` chart with no `max` no longer prints its tallest value twice). Fault 4 is by design (`catalogue.py` is a derived cache that must be rebuilt to see a new comic). Faults 3 and 6 and the missing assets are still open.

## Faults

1. **`check_quotes.py` cannot check a topic comic's bare `claims.yaml`.** `skills/source-to-claims` step 4 says to run it on `claims.yaml`, but with `--pages-root` it reads `doc["meta"]["sources"]` and dies with `KeyError: 'meta'` (a traceback, not a message). I worked around it by writing a temporary file that joined `head.yaml`'s `meta` to the claims. Suggest: accept a `--head` file, or say plainly that the input must carry `meta.sources` (and let `build_storyboard.py` be the way to check a topic ledger), and say so in the HOWTO table row "Pages for the quote check".
2. **The validator's "scene names a prop that is not staged" check cannot see props inside `staging.split`.** B2.1's scene said "a bottle ... a jar" and both were staged in the split halves; it warned twice (`mentions a bottle but no bottle prop is staged`). I had to reword the scene so it does not name the objects, which weakens the alt text. It should look into `split[0]` and `split[1]` as well (characters held objects too).
3. **`visual_qa.py` says "no defects found" although a prop's own label touches the prop's outline.** A `bottle` or `jar` `label` is drawn on the bottom edge of the bottle (the line passes through the label's top) in a tall box. I saw it in the PDF only. Fixed here by leaving the label off and using a separate `label` prop below. The scan compares text with text and panel edges, so it cannot see this (the visual-qa skill already says so).
4. **`catalogue.py --uses split|blackbox|bridge` printed "(nothing)"** (no comic used them then, so this is correct) **but running it rebuilds `private/catalogue.db`**, which the brief for this job said not to touch. The HOWTO says it "rebuilds `private/catalogue.db`" but a read-only query like `--uses` should not need to write. I ran it once before this was clear; the file is generated and gitignored.
5. **`bars` shows its maximum tick even when `max` is not set**, so a two-bar chart of 10.03 and 8.4 printed "10.03" twice. `show_max: false` fixes it, but the storyboard skill only mentions `show_max` for an axis maximum you cannot cite.
6. **`filter` (and other fixed-aspect props) in a tall split half draws small and low**, leaving a large empty box above it. Not wrong; the skill could say "do not give a split with fixed-aspect props `height: tall`".

## Missing assets (what I wanted and drew another way)

- **A range** (61 to 68 percent; 27 to 38 percent): `bars` takes one value per bar, so the replicate result is two `box` props. A bar or axis span with a `from` and `to` on a `bars` prop would draw ranges honestly.
- **A Venn whose overlap is proportional, or an overlap that can be small or large**: `venn` always draws two equal circles with a fixed overlap, so "the overlap was large" (51 species) could not use it; I used `stack` instead. The README says sizes mean nothing, but a reader still reads a small overlap as "little shared".
- **A `stack` that prints each segment's value** (it prints labels only). I put the numbers in the caption.
- **A way to flag one half of a split as "a different test"**: B5.1 puts two different comparisons side by side with `split_labels`; the comic's own caution ("these are different tests, not a contradiction") has to be in a caption.

## Things the skills did not say, that a cold run needs

- **A topic comic's beat plan.** The story-spine skill says "beats by theme, not paper by paper", but the clearest shape here was one beat per test (each paper changes a different thing), then a cross-paper beat for the side-by-side, then one for what is open. A line saying that a beat per paper is fine when each paper is a different kind of test, as long as a cross-paper beat follows, would have saved a rewrite of the plan.
- **How to cite a claim for an overview panel** (B1.4, "three studies, three tests") that only names the papers. I cited the three claims whose numbers or names the panel shows. The strip test flags it. The skill could say whether an overview panel may cite nothing.
- **`humour` placement for an `aside` device**: the validator treats a joke on an `aside` the same as any other, which is right, but the humour skill's "Callback lines" paragraph and the `aside` device's "adds no fact" description overlap; I left both of my lines as flagged jokes to be safe.
- **A caution on `shot: close` with `think` pose**: the head is cropped so far that the face reads as a mask; the paper's own question (B6.1) worked, but a `smile` or `neutral` close-up probably would not.
- **Naming the paper in every caption.** The topic rules say "name the paper in the caption", but a beat that is entirely one paper's results makes "In Clarke's study," on every caption clumsy. I put the name on every caption anyway, as the rule says, and shortened elsewhere.
