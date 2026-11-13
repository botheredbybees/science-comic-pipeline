# Skill feedback: a cold run on Lin et al. 2021 (Nature Communications)

Followed cold, in order, 2026-11-13, with `.venv/bin/python`. No script or renderer was changed (nothing blocked the run).
Result: 76 claims, 59 panels, 11 pages, PDF exported. Items are ordered by importance within each skill.

## Overall

- **Top five defects** (see the end for detail): (1) bar values printed with `%g` (25.0 shown as 25%); (2) prop fields
  undocumented (`items`, `cards`, `series`, `notes`...) outside the schema and `props.py`; (3) `weight` is only a
  preference, so a `wide` chart panel is silently squeezed to a third; (4) the claims locator format is not what the
  page map shows and only "paragraph N" is checked; (5) `fetch_source.py` truncates the licence statement mid-word and
  never shows it, and the "Done when" lines contradict the `abstract_only` status.
- The five-skill order worked. The rule that every number needs a cited claim caught nothing, because I wrote to it from the start;
  the visual defects were the surprises.
- The task brief mentioned an `ATTRIBUTION.md`, `CLAIM-CHECK.md`, `PLAN.md` and `QA.md "in the style the skills describe"`: only `CLAIM-CHECK.md`
  and `QA.md` are described, loosely; `ATTRIBUTION.md` and `PLAN.md` are not described by any skill (the root `ATTRIBUTION.md`
  only has a table). I followed the root table's columns.

## 1. source-to-claims

- **Unclear: confirming the licence "on the article text".** The skill says the script checks the licence; the brief said to
  confirm it on the article text. `fetch_source.py` prints only "Licence: CC BY 4.0 <url>". `source.json`'s `licence_statement`
  is cut at 300 characters mid-word ("... indicate if changes were ma"), and the text about third-party material (which is
  exactly what decides whether figures may be reused) is lost. I opened `PMC8368043.xml` by hand. Change: store the full
  `<license>` text in `source.json`, print its first sentence, and have the skill say so.
- **Wrong/contradictory: the "Done when" line.** "every claim is either `verified` or explicitly `unverified` with a note", yet
  the schema, step 2 ("`abstract_only`") and the storyboard skill all use a third status. Say what happens to an
  `abstract_only` claim at the end of this skill (I avoided the status).
- **Locator format.** The skill says a `locator` "is read straight off" `page-map.txt`. The map writes nested sections as
  `[Methods / Construct statistical models for NCP / Genetic programming ...]`; the checker splits the locator on ", ". My first
  C26 locator copied the " / " and drew a warning. Also `check_quotes.py` only checks locators ending "paragraph N" (its regex),
  so abstract ("abstract 1") and figure-caption locators are never checked. Change: say in the skill to join levels with ", ",
  and either check or say what to write for abstract and caption pages.
- **Single "Results and discussion" section.** This paper has no separate Discussion, so the skill's advice about "Results against
  Discussion" cannot be applied by section. I compared by paragraph instead (Results and discussion paragraphs 1 to 9). Mention that
  some journals merge them, and that `act:` in a beat is then a judgement, not a section name.
- **Missing: one claim = one contiguous quote.** The skill says "at least a clause long, containing every number in the claim" but
  not that the quote cannot skip text. Claims I first wrote from two sentences (C2/C3, the Southern Ocean sentence) could not be quoted and had to be
  split; C7 and C32 needed long multi-sentence quotes. Add: "if a claim needs two separate stretches, make two claims".
- **Slightly inconsistent: "empty brackets and all".** The skill insists the quote reproduce the page "empty brackets and all"; the
  checker ignores all punctuation and case, so it is not needed (and I kept `,,` in C2 only to be faithful). Say what the checker
  really tolerates, so nobody wastes effort.
- **Missing: figures matter here and cannot be read.** Fig. 2 (NCP maps), Fig. 3, Fig. 4 and Table S2 hold the central numbers (no NCP value
  appears in the text). The skill's answer is `unverified`, but it gives no route to the real values (Source Data files, the PDF
  with `pdftotext`/image views). The comic has no NCP numbers because of this. Add an optional step: fetch the PDF figures or the
  Source Data, or state plainly that a comic from XML text alone cannot chart the central result.
- **Good:** the conflict list ("things the text will do to you") predicted real findings here (sample counts, n = 6 against nine,
  "all significantly different"). Add "the title or abstract headline against what the design can show" (here: "Decline ... with
  reduced sea ice" against five years of moderately positive ice anomalies, p007), which is not in the list.
- **Missing: how many claims.** I wrote 76 (67 used). Fine, but a number or a rule of thumb ("about 1.2 claims per planned panel") would help.

## 2. story-spine

- **Unclear: the But when the only gap statement is in the abstract.** The skill points at the last Introduction paragraph. This paper's
  Introduction has no "little is known" sentence; "remain an open question" is only in the abstract. I used the Introduction's "it is
  imperative to understand and predict" (C5) plus the study-years caveat (C32). Say what to do (use the closest body sentence, never
  an abstract-only one).
- **Missing: titles are claims too.** My first title ("Less Ice, Fewer Kinds") overstated the paper (the diversity result is with SST; ice is one of two
  linked drivers). Nothing in the skill or the validator checks `meta.title`. Add a rule: the title must be supportable by a claim.
- **Contradiction: jargon rule.** "Use the paper's own gloss ... If the paper gives none, keep the term and list it in `left_out`, or
  leave it out." Chao1, Pielou's evenness, Shannon and CCA have no gloss (only "Chao1, a measure for species richness"). Keeping
  five such terms and listing each in `left_out` is silly; say that a one-clause gloss from the paper counts, and that an
  unglossed statistical name is allowed in a caption when the claim around it says what it does.
- **Unclear: `hair_tone: strands` "both are blond".** At the rendered size Wren's long strands read as scribbled dark hair, not blond.
  Show the three tones in renderers/README as a picture or say how they read. Distinct cast was easy with `hair`, `glasses`, `coat`, `holding`.
- **Missing: planning a chart.** The beat table has no column for "chart or prop", so the plan cannot say where the bars and the
  schematic go; I added "charts are the point" in the rhythm column. Add one.
- **Spine length.** "three sentences" is not achievable for a data-rich paper; mine run long. Allow a short list after each.
- **Good:** the "do not invent a villain" paragraph; the study-years caveat came straight from it.

## 3. storyboard

- **Missing: the prop field vocabulary.** `renderers/README.md` lists prop kinds (`board`, `flow`, `axis`, `plot`, `bars`...) but not
  their fields: `axis` takes `items` with `at`, `to`, `style` (solid, hollow, mark) and `row`; `flow` takes `items` with `label`;
  `board` takes `cards`; `plot` takes `series` with `points`, plus `notes`, `x_label`, `y_label`; `bars` takes `bars`, `min`, `max`,
  `show_max`. I had to read `renderers/xkcd/props.py`. Document each with a one-line example.
- **Unclear: `weight` is a preference.** The skill says "a chart with several bars is better in a `wide` or `full` panel". In the render a `wide` panel
  (B4.1 got 4 of 12 units because the row packer preferred 4+4+4; B3.2 got about 6) and the squeeze made labels collide (the scan caught B3.2 only once). Only `full` guarantees a width. Add: "if a panel must be wide, use `full`" or add a `min_units` hint.
- **Defect: numbers lose their zeros in a chart.** `bars` prints `{value:g}`: 25.0 shows "25%", 14.0 "14%", 19.0 "19%". The skill's own rule is
  "numbers go in verbatim". The validator cannot see it (it checks the YAML, not the SVG).
- **Contradiction: caption 12 to 35 words / "split rather than trim".** C79's sentence is one conditional ("To the extent that ... could be
  destined for ..."); trimming drops the hedge, splitting drops the sense. B6.10 is 40 words and B2.3 is 11. Say a single hedged
  clause may exceed 35 words; the validator does not check length at all (I counted by script).
- **Unclear: "Read the preview as a stranger".** The preview is a web page; no instruction how to open it (needs a browser, fonts from Google). I wrote it
  and judged the story from the PDF. State the command to open it, or drop it from "Done when".
- **Missing: a clean-up of `--keep` output.** If the page count changes, stale `page-N.svg` files may remain in the keep directory; I deleted the directory before each run.
  (Not tested whether the script handles it; say so either way.)
- **Good:** "Cite every claim a panel relies on, nothing it does not" and the unused-claims list are useful and consistent now. The validator's
  scene-versus-staging check caught my "ship's rail" scene. The skill's character scale advice (krill 1.3) was right.
- **Suggestion:** a `scene` check for `clipboard`, `mug` and speakers' names, which is where I could have gone wrong (the validator only checks nine object words).

## 4. humour-pass

- **Confusing: the five answers have mixed polarity.** "1 no change; 2 reads as the comic's voice; 3 organisms; 4 no; 5 yes": a pass is "no" for questions 1
  and 4 and "yes" for 5. Reword so every pass is "yes" (or every pass "no").
- **Missing: a joke on a panel that cites no claim.** The text says the warning applies "on a panel with claims or without"; an example would help.
- **Unclear: when to set `true`.** The brief and the skill both say leave `false` when unsure. I set one joke `true` (B2.3, a gag about Teo's
  tea beside a method fact, nothing about plankton) and two `false` (a smug diatom, and a tea callback next to a caveat). The skill does not say that
  a callback beside a *caveat* should default to `false`; it only says "does it play down a caveat" (question 4), which is a judgement.
- **Missing: "Say in `CLAIM-CHECK.md` where the comic added its own aside"** has no template; I added a short section.
- **Good:** "exit 1 is the right end state" is clear and was true (2 warnings).

## 5. visual-qa

- **Good:** the checklist predicted most of what I found (text through a sign's border, charts, narrow boards, pages with half-empty rows).
- **Missing: things not on the list that happened.** A character's held clipboard overlapping the next prop (B2.4, B5.4, B6.4); a chart with a scale larger
  than its data (empty half panel, B5.15); a panel that the packer made narrower than its `weight` (see above); a plot note wrapping between a number and its
  unit ("4 / °C", B4.1). Add them.
- **Unclear: "compare the PDF with the sheet once".** `sheet.html` is one page with all SVGs; no instruction how to view it. I counted pages (11 SVGs, 11 PDF pages) only.
- **Unclear: "Do not stop at the first clean scan".** I fixed 11 things by eye after the scan said "no defects found"; fine, but the skill could say the
  scan only compares text with text, so expect most fixes to come from the eye pass (it already says this in a list; make it the first sentence).
- **OK:** `pdftoppm -r 70` is a bit small for chart labels; 80 to 110 was needed for bar value labels.

## The five defects to fix first

1. **Renderer: `bars` value labels use `%g`** (`renderers/xkcd/render.py`, `_bars`), so a paper's 25.0, 23.0 and 14.0 are drawn as 25%, 23% and 14%. Keep the source's decimals (an optional `decimals` or format the YAML string).
2. **Docs: prop fields are not documented** (`renderers/README.md`); `axis`/`flow`/`board`/`plot`/`bars` need their field lists and an example each.
3. **Layout/skill: `weight` is a preference only**; a chart panel marked `wide` can be given a third of a row and then collides. Document `full` as the only guarantee or add a minimum width.
4. **Checker/skill: locators.** The page map joins levels with " / " while the checker wants ", "; only "paragraph N" locators are validated; merged "Results and discussion" sections are not discussed.
5. **fetch_source/skill: the licence.** The statement is truncated mid-word in `source.json` and not printed; and the "Done when" lines ignore the `abstract_only` status the rest of the pipeline uses.
