# Claim check: Strzepek et al. 2022

Date: 2026-11-13.

## Source and licence
- Strzepek RF, Nunn BL, Bach LT, Berges JA, Young EB, Boyd PW (2022). *The ongoing need for rates: can physiology and omics come
  together to co-design the measurements needed to understand complex ocean biogeochemistry?* J. Plankton Res.
  DOI 10.1093/plankt/fbac026, PMC9310281.
- Fetched with `scripts/fetch_source.py --doi 10.1093/plankt/fbac026 -o sources/strzepek-2022` (Europe PMC full-text XML,
  26 paragraph "pages"). The script printed `Licence: CC BY 4.0 https://creativecommons.org/licenses/by/4.0/`; the same
  statement is in the XML's licence element ("distributed under the terms of the Creative Commons Attribution License ... unrestricted
  reuse"). Licence confirmed by script, 2026-11-13; no PDF was read.
- "Page" in `claims.yaml` is the paragraph file number (`p019` = page 19), not a journal page.

## Results of the checks
- `check_quotes.py examples/strzepek-2022-rates/claims.yaml --pages-dir sources/strzepek-2022/pages --strict`: 65 claims, 0 errors, 0 warnings.
- The same on the built `storyboard.yaml` (51 cited claims): 0 errors, 0 warnings.
- `validate_storyboard.py --strict`: 0 errors, 1 warning. The warning is B1.2's joke, left `keeps_claims_intact: false` on purpose for a
  human to decide (see humour below).
- 64 of 65 claims are `verified` (quote on its page, checked by script). C61 is `unverified` and kept out of the panels.

## Second pass (reading each claim against its quote)
- C26 first said "more proximal ... than genomics"; the quote does not say that. Cut the comparison, added a note.
- B1.1 first said models "count in two currencies"; the quote says the currencies "include" rates and fluxes. Reworded.
- B5.5 first had the modeller say "Now that I can use." about P quotas; C34 says physiological *rates* are in units modelers can use, and a
  quota is a metric, not a rate. Changed to "A converter!".
- C48's quote is a clause inside a question ("Will such co-designed metrics reconcile ... since different physiological metrics display a
  range of response times"). The panel states it as the authors' point, which the clause supports, but it is not a standalone sentence.
- Cited work cannot be named: the Europe PMC text has the in-text citations removed, leaving `()` and `(; )`, and in places the subject is
  missing ("in a lab-based investigation ... demonstrated"). So panels say "a study" or "a critique the authors cite" and never name the researchers behind cited work.

## Things in the paper that disagree with themselves
1. **Fig. 3 caption against the body.** Body (p19): proteomics showed *lower* expression of P-containing translation proteins under warming
   and *lower* cellular P quotas. Fig. 3 caption (p14, panel A): "Higher (downward arrows) and lower expression (upwards arrows) ... Warming
   results in higher expression of P-containing proteins associated with translation." The caption's arrow convention is also the reverse of
   what a reader expects. Panel B of the same caption says "lower expression of translation proteins and decreased P quotas". So the caption
   contradicts itself and the body. The comic follows the body (C37, C38). Recorded as C61 `unverified`, not used.
2. **"subpolar" against "subantarctic".** Body p19: "a subpolar diatom"; Fig. 3 caption p14: "a subantarctic diatom". Panels say "a diatom".
3. **"five stressors" against "4 treatments".** Body: "five climate-change stressors"; caption: "4 treatments within a climate change manipulation
   experiment" (treatments A to D). Not necessarily a conflict (stressors and treatment groups), but the comic uses only "five stressors" (C35).
4. **Abstract against body.** No disagreement found. The abstract's "unlikely that omics can provide such rates in the coming decade" is repeated
   as an opinion in the body; there is no data behind it, only the case studies and the biomedical trajectory. C10 and the closing panels
   say so ("the authors conclude", "in their opinion").

## What the paper cannot give a comic
- It is a perspective: no new data, and no "limitations" paragraph. Its caveats are in the open questions (C46, C47, C48) and in the
  repeated "in our opinion" / "may be" wording (C43, C45, C56). All are in the panels.
- Anything in Figs 1 to 5 beyond their captions (values, pathway detail) is `unverified` by definition and not used. The comic's two charts
  (mRNA against protein; derived nitrite-oxidation rates) are labelled schematic and carry no values. The only number is ">200-fold" (C52).

## Where the comic adds its own voice (not the paper's)
- The whole **exchange-booth conceit**: the desk, the signs, the "converter" sign, the characters (modeller, physiologist, omics researcher,
  Dot). It is built on the paper's words "currencies" and "currency converter" (C1, C9, C39); the paper describes no booth or characters.
- **Dialogue lines** that comment but add no fact: "Rates and fluxes. Those are our main coins." (C1), "Still here.", "Obsolete?" (C7's word),
  "That is a lot of data.", "Different currencies.", "Rates in, fluxes out." (C14/C15), "Genes aren't rates." (C18), "What about expression?",
  "Noted.", "So biomedicine hasn't solved it either." (C55), "Activity ultimately drives the cycles." (C32), "Over two hundred fold." (C52),
  "That's me.", "Lower, as well.", "A converter!", "Lucky.", and the physiologist's paraphrase of C42 in B6.2.
- Captions that expand an abbreviation the paper itself uses: "P (phosphorus)" (C13), "diazotrophy (nitrogen fixation)" (C64).
- B4.1's two wavy lines are an invented schematic, labelled as such; they are not Fig. 2's data.
- The colophon says the characters are invented and the authors did not write or endorse the comic.

## Humour (3 proposed, one per beat at most)
| panel | joke | judged | human to look at first? |
|---|---|---|---|
| B1.2 | physiologist deadpans "Still here." beside "have not fundamentally changed in decades" | unsure whether the authors, several of them physiologists, would take it as teasing their field | yes; left `keeps_claims_intact: false` |
| B2.2 | a second pile of printouts labelled "more" beside "a surfeit of data" | safe | no |
| B5.6 | Dot shrugs "Lucky." beside "serendipitously" | safe | no |
