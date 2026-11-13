# Claim check: Pauli et al. 2021

- **Date:** 2026-11-13.
- **Source:** Pauli NC, Metfies K, Pakhomov EA, Neuhaus S, Graeve M, Wenta P, Flintrop CM, Badewien TH, Iversen MH, Meyer B (2021). Selective feeding in Southern Ocean key grazers: diet composition of krill and salps. *Communications Biology*, doi 10.1038/s42003-021-02581-5 (PMC8433442).
- **How obtained:** `python scripts/fetch_source.py --doi 10.1038/s42003-021-02581-5 -o sources/pauli-2021-krill-salps-diet` (Europe PMC full-text XML, 46 numbered pages). The licence gate printed "CC BY 4.0" and did not refuse.
- **Licence, read on the article text:** `source.json`'s `licence_statement` reads "Open Access This article is licensed under a Creative Commons Attribution 4.0 International License, which permits use, sharing, adaptation, distribution and reproduction in any medium or format, as long as you give appropriate credit ..." (from the article's own licence statement, not only the script's classification). Recorded in `head.yaml` `licence_checked`. The figures were not inspected for third-party material (the XML has no figure files); the comic redraws every chart from text values.
- **Ledger:** 66 claims (C1 to C81 with gaps: 15 claims that no panel used were dropped, as the storyboard skill says; ids were not renumbered). `check_quotes.py --strict`: 66 checked, 0 errors, 0 warnings. 64 are `verified` and drawn; C80 and C81 are `unverified` and not drawn.
- **Second pass done by reading:** each claim read against its quote. Weakened or reworded: C1 (quote widened to include the species names), C24 (the "CTD rosette" detail dropped because the quote did not carry it), C34 (an "after the dinoflagellates" ranking removed).

## Internal conflicts in the paper

| Where | What | What the comic does |
|---|---|---|
| Results p. 13 vs Discussion p. 27 | Crustaceans are 26.5% of krill stomach sequences in the Results, "about one third" in the Discussion. | Uses 26.5% (C37). "About one third" is C80, `unverified`, not drawn. |
| Discussion p. 26 | "salp FP contained a considerably higher share of diatoms than krill pellets (36.2% vs. 13.9%)". The Results (p. 15) give 13.9% as the *Dinophyceae* share of krill pellets, and say only that diatoms were "reduced" in krill pellets. | C81, `unverified`, not drawn. The salp pellet diatom figure used is the Results' own (36.2% vs 7.4% in salp stomachs, C66). |
| Results p. 19 vs Table 2 | Dinoflagellate marker fatty acids: text p = 0.665, Table 2 p = 0.661 for the same test. | The panel gives no p-value for that claim (C54). C53's p = 0.002 agrees between text and table. |
| Results p. 11 vs Discussion pp. 22, 30 | ANOSIM found "significant differences between all sampling groups" (p = 0.01), yet the Discussion says "there was no significant difference between krill and salp diet composition". The paper does not say which comparison reconciles them (stomach versus pellet clusters "largely overlapped"). | The comic states C45 ("largely overlapped") and C62 as the authors word them, and the abstract's hedge for the competition claim (C60, "broadly similar", "potentially"). It does not say the diets were identical. Flag for a human. |
| Abstract vs Discussion p. 30 | Abstract: similar diets "potentially enhancing the competition". Discussion: salp traits "enable salps to outcompete krill. This poses an additional threat to krill populations." | The comic follows the abstract's hedge only (C60, C61). |
| Results p. 12 vs Discussion p. 29 | Syndiniales in the plankton: "about 5%" and "4.9%". | The chart uses 4.9% (C73). |

## Where the comic added its own aside or cross-reference

- **Sal is a stick figure.** The renderer has no salp body, so the salp is drawn as a plain stick figure. `head.yaml` says so in the cast; the comic itself does not, so a reader may think a salp looks like a person.
- **Mara's lines** ("Meet the two grazers.", "Time to go fishing for krill and salps.", "Selective? What does that mean?", "So lunch does not match the water?", "So salps are picky too?", "Krill eating salps?", "Attached, but not seen eating.", "Or the animals had been infected before.", "So some diatoms do get absorbed.", "So nobody has put them side by side?") are the comic's voice; each is a question or a restatement of the cited claim, not a new fact. "Attached, but not seen eating" compresses C71 and C72.
- **Kip's line** "Copepods, at every depth." restates C51 in the krill's voice.
- **Jokes (flagged, `keeps_claims_intact: false`):** Sal's "I have standards." (B4.5) and "Don't look at me." (B6.1).
- **Bowls** stand for food in B1.6, B1.7, B5.4, B6.5; no claim says krill and salps eat from bowls. The pair of bowls in B1.7 is drawn the same for both animals (it does not show who is selective).
- **Whale and penguin** in B1.2 illustrate C2 ("whales, seals, and penguins"); seals are not drawn.
- **Axis in B1.5** is marked "schematic, not to scale": the 60°S and 65°S positions are drawn at 0.2 and 0.8 of the axis, not at scale.
- **Ivlev axes (B4.2, B4.3)** place each dot at (value + 1) / 2 of the axis, so positions are to scale; labels are grouped (one label for several dots) because crowded labels collided.
- **Colour of krill and salp bars:** solid = krill, hollow = salp in B2.4, B3.6, B5.1; the plankton charts are solid. This is the comic's convention (the paper uses red and blue); it is not stated in the comic.
- **Chart axis maxima** are the largest bar's own value (e.g. 39.5%), which is a number in a cited claim; charts are not on a common 0 to 100 scale, so bar heights should not be compared across panels.

## Claims judged unverifiable or not used

- C80, C81 (see above): `unverified`.
- Not drawn, by choice: the fecal pellet compositions (krill pellets 56.4% small flagellates, salp pellets 36.2% diatoms and 33% flagellates); the copepod fatty acid markers (salp tissue higher than krill, p < 0.001, which sits awkwardly beside krill's copepod-rich stomachs); lipid content (6.7% in krill vs 0.97% in salps); sex and length effects. See `left_out`.
- Figure-only values (anything read off Figs. 1 to 6) were not used.
