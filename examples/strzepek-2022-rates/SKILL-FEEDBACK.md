# Skill feedback: following the five skills cold on Strzepek et al. 2022

Paper: a perspective article (no new data). Result: 65-claim ledger, 6 beats, 36 panels, 6 pages. Everything below happened while
following `skills/README.md` and each `SKILL.md` as written. Ordered by skill; the biggest items are repeated at the end.

## 0. README and set-up

- **Every command in the skills says `python scripts/...`.** The repo needs `.venv/bin/python` (jsonschema, yaml). A cold reader with a
  system python gets an ImportError. README should say "run these with the repo's venv" once.
- README says "Run them in this order" and shows `claims.yaml, CLAIM-CHECK.md` as skill 1's output, but skill 1 step 5 also says to
  "Fill `meta.source` ... from `source.json`", and `meta` lives in `head.yaml`, which skill 2 writes. At skill 1 there is no file to put it in.
  Either move that sentence to skill 2 or say "keep the source.json values for later".

## 1. source-to-claims

What I did: ran `fetch_source.py --doi 10.1093/plankt/fbac026 -o sources/strzepek-2022` (printed `Licence: CC BY 4.0`, 26 pages), read all 26
paragraphs, wrote 61 claims then added 4 more during later steps, ran `check_quotes.py` until clean, did a read-through of each claim against
its quote, wrote CLAIM-CHECK.md.

Friction:

1. **The fetched text has its citations stripped.** Every citation became `()` or `(; )`, and some sentences lost their subject ("This
   misalignment was illustrated in while tracking diel changes"; "in a lab-based investigation ... demonstrated"). Consequences nobody warns
   about: (a) a quote must reproduce the empty parentheses to match; (b) the comic can never name who did a cited study; (c) a reader of the
   comic cannot tell "the authors found" from "a study they cite found" except by my wording. The skill says "Separate what the authors
   found from what they cite" but gives no way to do it when the cite is gone. **Add:** a warning in step 1 that Europe PMC XML text drops
   in-text citations; tell the writer to attribute as "a study the authors cite" and to record in CLAIM-CHECK.md that cited work is anonymous.
2. **A false-positive warning from the number check.** Claim text "The Fig. 3 caption says ..." gave `WARNING C61: number(s) 3 in the claim are
   not in its quote`, and "Fig. 2 shows..." likewise for C59. The skill says "Fix every error and warning", so I removed the figure numbers
   from the claim text. Harmless, but the rule is not stated: **add "do not put figure or table numbers in claim text"**, or make the checker
   skip `Fig. N`.
3. **No place for a source that contradicts itself.** The Fig. 3 caption says warming gives *higher* expression of P-containing proteins; the
   body says *lower*. The caption's quote is genuinely on its page (so the checker would pass it as `verified`), but I did not want a verified
   claim that contradicts another verified claim. I used `status: unverified` with a note. That muddles two meanings ("quote not found" and
   "found but conflicts"). **Suggest** a rule in step 3 ("when text and caption disagree, record both, mark the conflicting one
   unverified with `note: conflicts with Cn`") or a fourth status. Also `abstract_only` is in the schema and the example but never explained in
   the skill.
3b. Skill 1's "A claim that only a figure shows ... is `unverified` ... never `verified`" is easy to follow, but it does not say what to do with
   a claim about what a *caption* says (that is text). I decided captions are verifiable text and values read off a figure are not.
4. **Definitions and glosses must be claims, but the skill never says to collect them.** Skill 2 says a general reader needs "a term explained
   once, in a caption, the first time it appears", and skill 3 says nothing in a panel may be outside the ledger. So the paper's own
   definition of "omics" (the genome, transcriptome, proteome and metabolome), what CMIP is (Coupled Model Intercomparison Project), what
   "diazotrophy" means, and what P stands for must be ledger claims. I only noticed when writing panels and had to go back and add C62 to C65.
   **Add to step 3:** "collect the paper's own definitions of its key terms as `background` claims, so the story step can explain them."
   There is also no way to gloss a term the paper never defines (e.g. "proteomics" for a lay reader); I left it unexplained.
5. **Perspective papers do not fit `method | result`.** There is no method or result in an argument paper. I used `method` for "the authors
   use three approaches" and "a lab study used...", and `result` for findings of cited studies. The skill ("methods in a sentence each, every
   result you might draw") assumes a research paper. **Add** two sentences for opinion/review papers: most claims will be
   `background`, `interpretation` and `caveat`; use `interpretation` for the authors' own arguments and keep "in our opinion" / "may be"
   in the claim text. (I did, because the hedges are the content here.)
6. **Quote rules that no script checks.** "at least a clause long", "must not start or end on a word with a digit stuck to it": nothing
   enforces them. Fine, but the "Done when" reads as if the checker covers everything. The real safety is the manual second pass, which found
   three overstatements the script could not: C26 ("more proximal than genomics"; the quote has no comparison), B1.1 ("two currencies"; the
   quote says currencies "include" rates and fluxes) and B5.5 (a phosphorus quota called a rate). The second pass is the valuable step and
   deserves a checklist: *comparisons, "only", "all", counts, "caused", metric versus rate*.
7. **No guidance on ledger size.** I wrote 65 claims, 51 were used. Is that right? A line like "expect to use about half" would help.
8. Step 4's command has no `--strict`, but "Done when" requires 0 warnings and skill 3 uses `--strict`. Put `--strict` in step 4.
9. "Page" means the paragraph file number, not a journal page. The skill says "A claim's `page` is that number" once; the schema calls it "the
   numbered page of the source text". I found this fine but the word is misleading for a citation: a reader may think it is journal page 19.
   Also `locator` ("Linking physiology and omics, paragraph 2") has to be built by hand from page-map.txt with a manual paragraph count.
10. The licence step worked well: the script printed it first, `source.json` carries `licence_checked`, and step 5 says where to note it.

## 2. story-spine

What I did: wrote audience, spine, cast, left-out, a six-beat plan with claim ids and a "conceit" (a currency-exchange desk, built on the
paper's own "currencies" and "currency converter" wording).

Friction:

1. **No example of `head.yaml`.** The skill says `meta.spine` is "three sentences" but the schema wants an object with `and`, `but`,
   `therefore`; `meta.source.year` must be an integer while `source.json` gives the string `"2022"`; `left_out` is "required in practice" but
   optional in the schema. I read `schema/storyboard.schema.json` to write it. **Add a 20-line skeleton** (or point at the schema).
2. **Cast guidance does not match the schema.** The skill says `appearance`: "hair, glasses, lanyard, hat". The schema has no `hat`, and hair is
   an enum (`none | ponytail | bun | spiky | beanie`). A `hat` key would fail schema validation. Also "`body: diatom | krill | penguin | whale` are
   drawn" omits `stick`, the default human.
3. **What is the cast for a paper with no organism and no field party?** The skill says a guide is "a person in the paper's world (a scientist on
   the ship, a student)". My guide is an invented "modeller" and I added a "physiologist" and "omics researcher" who stand for research
   communities. The skill does not say whether archetypes are allowed, whether they must be flagged as invented (I added a line to the
   colophon text in `left_out` and CLAIM-CHECK.md), or how to personify a *community* without implying a feud the paper does not describe. The
   paper does not say the communities quarrel, so I made them courteous. **Add:** "archetype characters are fine; label them as invented; do not
   let a character embody a group in conflict unless the paper reports one."
4. **The "little conflict" paragraph is the best part of this skill, and is written for result papers** (a negative result, a method that nearly
   failed). A perspective's tension is a mismatch of aims (here, "currencies" of models against omics). One more example would help. I
   found "the real tension is that the case studies show the exchange does not work yet" only by re-reading the paper.
5. **Claim ids in the spine strings.** I put `(C1, C2, ...)` in each `and/but/therefore` sentence to meet "uses only claims from the ledger".
   `validate_storyboard.py` does not check the spine at all (it passed "200", "15N" and "N2" without comment), and `preview_storyboard.py`
   prints the ids to the reader. If ids in the spine are expected, say so; if not, say "the spine is checked by eye only."
6. **The plan drifts.** My PLAN.md listed C20 under B3; when I wrote panels I dropped it and added C65 to B1. Nothing reconciles PLAN.md with
   the storyboard. Suggest ending the storyboard step with "update PLAN.md's claim ids to match what the panels cite", or generate the table.
7. `meta.left_out`: useful. I used it to record that the exchange-booth setting is the comic's own conceit. Say that this is where framing
   metaphors go (skill 4 does not).

## 3. storyboard

What I did: wrote six beat files (36 panels), built, validated, previewed.

Friction:

1. **`preview_storyboard.py examples/<slug>/storyboard.yaml` as printed fails:** `preview_storyboard.py: error: the following arguments are
   required: -o/--out`. The skill's command has no `-o`.
2. **The skill's "unused claim is a warning" rule does not fire.** The skill: "A claim in the ledger that no panel uses is a warning". But
   `build_storyboard.py` copies only the cited claims into `storyboard.yaml`, so the validator never sees the rest. The only signal is a
   count in the builder's output: `51 of 65 ledger claims used`. I listed the 14 unused ids by hand in PLAN.md. Either print the unused ids
   from the builder, or fix the sentence.
3. **Spelled-out numbers evade the number rule.** The rule is "A panel whose text ... contains a number must cite a claim whose text or
   quote contains that number". The validator checks digits. A panel saying "Over two hundred fold." (supported by ">200-fold") is not
   checked at all, and it would not be if I had written "three hundred". **Add:** "write numbers as digits in panels so the check sees them" (or
   extend the check to number words beyond ten).
4. **Nothing checks that `scene` (alt text) matches the staging.** My first draft's scenes mentioned a calendar, an ocean, a ship icon, a flask
   and a bridge that the staging never drew. `holding` only allows `marker | mug | paper`, so my "flask" was drawn as a mug. I found these only
   by looking at pages. Add to "Rules": "the scene must describe what the staging draws, since it is the alt text."
5. **Staging vocabulary is learnt only by rendering.** `renderers/README.md` lists the kinds but not the behaviour that cost me fix cycles:
   - `sign`: the label sits in the top half of `h` only and wraps at `w`; a 24-character label overflowed the sign twice.
   - `label`: `x` is the *centre* of the text, not the left.
   - `arrow`: ignores `w`/`h`, uses `x2`/`y2`.
   - `board` cards and `box`/`flow` labels shrink to about 9 pt in a narrow panel (the "Crocosphaera" card, the "biochemistry" card).
   - `axis`: an `at`/`to` bar with `style: solid` is a black bar that hides the neighbouring tick labels; use `hollow`, and use plain ticks
     (no `style`) for the end labels.
   - `plot`: needs `x_label`/`y_label`, `notes` at fractions; the lines are dashed/dotted only, so a "schematic" panel is easy.
   A short table "prop, what `w`/`h` mean, text limits" in `renderers/README.md` would have saved most of my visual-QA fixes.
6. **Panel weights decide figure sizes more than the staging does.** A `small` panel in a row with a `wide` one produced a narrow, tall panel
   with a tiny figure (B1.3, B3.7) and a `standard` panel produced a 9 pt card (B3.3, B4.5). The skill says "Figures scale with the panel's
   height" only in the renderer README. **Add to the skill:** "text-heavy or chart panels need `wide`; use `small` only for a panel with no
   staging."
7. The panel field list is long (`weight`, `frame`, `height`, `transition`, `word_picture`). `word_picture` is optional and needs McCloud's
   vocabulary; I filled it in a few places and cannot tell if I was right. Say "leave it out unless you know what it means" or explain in one
   line each.
8. The "12 to 35 words" caption guide is not checked. Mine ended at 32 words at most (B4.1), but only because I split long claims; a claim
   longer than 35 words has no stated recipe (split across panels, or shorten without strengthening). Say which.
9. A good thing: the validator accepted the first complete build (`0 error(s), 0 warning(s)`), and the "keep the hedge" rule pushed me to write
   "the authors think", "in their opinion", "may be" into captions. It worked.

## 4. humour-pass

What I did: proposed three jokes (B1.2, B2.2, B5.6), wrote the five-question notes, set two `keeps_claims_intact: true` and left one `false`
because I was not sure the authors would like it.

Friction:

1. **Contradiction between "leave it false when unsure" and the done condition.** Step 4 ends: "Leave `keeps_claims_intact` false, and the
   humour block in place, when you are not sure." The Output section says: "Re-run `validate_storyboard.py --strict`; every joke on a cited panel
   must be flagged." The validator warns on a `false` joke on a cited panel (`WARNING B1.2: joke on a panel that cites C5; a reviewer must
   confirm it keeps the claims intact`) and `--strict` exits 1. So following the skill honestly produces a failing strict run, and storyboard's
   "Done when: `validate_storyboard.py --strict` ... clean" cannot hold. Choose one: have strict ignore `false` (it is waiting for a human),
   or say a pending joke is expected to leave one warning, or say remove any joke you are unsure of. I left the warning in and reported it.
2. **Framing metaphors are not covered.** The whole comic is an exchange desk. Is that "humour" needing a block? It touches no claim, but it is the
   comic's own voice. I put it in `left_out` and CLAIM-CHECK.md. Say where such a conceit is declared.
3. **Question 3 ("Who is the butt?") assumes organisms or instruments**, but in a paper about two research communities the stock characters
   are people groups. "Still here." (physiologist) and "Obsolete?" ride close to the line: the authors' own abstract says physiology
   "has stagnated". I wrote that the authors might read it as teasing and left it for a human. The skill should name this case.
4. "Raw material" list is built for results ("a 4.3% group with 78% of the reads"). A perspective offers almost none; the best material
   was the authors' own words ("surfeit", "serendipitously", "obsolete"). Add "single loaded words from the authors".
5. "Say in CLAIM-CHECK.md where the comic added its own cross-reference or aside" is good and I followed it, but the file is not mentioned in
   skill 1's description of CLAIM-CHECK.md or in the README; discoverability is low. One mention in skill 1 step 5 would do.

## 5. visual-qa

What I did: rendered, ran `visual_qa.py`, converted every page to PNG and looked at each (twice), fixed 14 defects in staging, re-scanned,
exported the PDF.

Friction:

1. **The command as printed crashes.** `python scripts/visual_qa.py examples/<slug>/storyboard.yaml --keep output/<slug>` with a *relative*
   `--keep` gives:
   ```
   RuntimeError: the scan produced no result (did the page load?)
   ```
   Cause: `scan()` builds `f"file://{probe}"` from the relative path, so Chrome gets `file://output/...`. Running Chrome by hand on the same
   probe with an absolute path worked. With `--keep $PWD/output/strzepek-2022-rates` the scan ran. Fix the script (`probe.resolve()`), or the
   skill ("use an absolute path"). I lost several minutes thinking Chrome was broken. (I did not edit the script, per the rules.)
2. **No recipe for "view a page as an image".** The skill says "a way to view a rendered page" but gives none. I used
   `google-chrome --headless=new --no-sandbox --screenshot=pN.png --window-size=794,1123 page-N.svg`. My first try with a 1000 x 1415 window
   showed the A4 page (794 x 1123 px) with a big white band under it, and I nearly recorded "blank band at the bottom" as a defect on every page.
   Give the command and the size. Also warn that `output/<slug>` is created outside the working folder (it is git-ignored).
3. **The scan said `no defects found` on a page set that had 13 defects.** It was clean on the first run (7 pages, 123 text items) while the
   pages had a sign label running through the sign's border, a black bar hiding axis labels, a speech line over a picture, 9 pt card labels and a
   last page holding one panel. The skill does say the script "cannot see" drawings, which is true, but the most common defects here were
   *text overflowing its own prop*. Suggest the scan also test each text's box against the prop rectangle it belongs to (the SVG groups would
   allow it).
4. **Font.** The machine had no Patrick Hand, so Chrome rendered the SVG in a serif fallback and text widths in the scan and in my review are
   not the real ones. The skill's "known limits" mention a font fallback but not that it silently changes the result. Check `fc-list | grep -i
   "patrick hand"` or embed the font.
5. The "last page nearly empty" check had no entry in the fix table. The first render was 7 pages with one panel and the colophon on page 7;
   changing three panels' weights (to `wide`) brought it to six full pages, but that was luck. Add a row: "last page nearly empty:
   change `weight` on a few panels so the packer finishes a page earlier."
6. Character scale: the same character is drawn at very different sizes in neighbouring panels (scale 0.65 in B3.4 and 1.5 in B1.3 to fill
   different panel shapes). The skill's list does not mention continuity of character size.
7. Good: the defect table ("Text over a drawing -> move the prop") matched what I needed, and "Do not stop at the first clean scan" was right.

## The five most important fixes (summary)

1. **visual_qa.py crashes on a relative `--keep`** (the exact command in the skill). Fix the script or the example.
2. **Humour: "leave false when unsure" vs `--strict` cannot both be satisfied.** Pick one rule.
3. **source-to-claims: tell the writer that fetched text has no citations, and to collect the paper's own term definitions as claims.** Both
   cost rework (C62 to C65 added late; cited work cannot be named).
4. **storyboard: the stated "unused claims warn" and "numbers need a claim" checks are weaker than written** (unused claims never warn since the
   builder drops them; spelled-out numbers pass; scene/alt text is never compared with the staging). State the limits, or tighten the checks.
5. **A staging cheat-sheet** (sign/label/arrow/axis/board/flow behaviour, text limits per panel weight) in `renderers/README.md`, plus a
   head.yaml skeleton and the correct `appearance` enum in story-spine. Most of my time went on schema reading and render-and-look cycles.
