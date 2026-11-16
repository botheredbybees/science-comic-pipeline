# Claim check: Does eDNA agree with itself? (topic comic)

- **Date:** 2026-11-16.
- **Sources:** three papers, all CC BY 4.0, already fetched into `sources/<id>/` (page text and `source.json`). Suter et al. 2021 (not open access) was not used.
- **Where the claims came from.** Earlier one-paper runs exist in `private/<id>/claims.yaml`. They were read only to find claims. For this comic each chosen claim's quote and page were copied into `claims.yaml` here, renumbered C1 to C40 with a `source.ref`, and **every quote was checked again against the page file**: `check_quotes.py` on the whole ledger (40 claims, 0 errors, 0 warnings) and on the built storyboard. The new folder's claims are the only ones the comic cites. Several quotes were also read by eye on their pages while writing the panels (Clarke p22 to p27 and p49, Nester p4 to p7, Blanco-Bercial p34, p35, p56 and p57).
- **Ledger:** 40 claims, all `verified`: 13 Clarke et al., 12 Nester et al., 15 Blanco-Bercial et al. All 40 are cited by a panel.
- **Page basis.** Clarke et al. and Blanco-Bercial et al.: the numbered paragraph/table files of the Europe PMC XML (`page` is that file's number). Nester et al.: the PDF page index.
- **Year.** Blanco-Bercial et al.: 2026 (the paper's own reference line, *Mol Ecol Resour* 26(1): e70090); Europe PMC's record says 2025.
- **Figures not seen.** The text pipeline reads no figures. Nothing in the comic is a value read off a figure. The charts redraw numbers that a cited claim states.

## Map from this ledger to the earlier ledgers

| Claim here | Paper | Id in `private/<paper>/claims.yaml` |
|---|---|---|
| C1 | Clarke 2021 | C14 |
| C2 | Clarke 2021 | C15 |
| C3 | Clarke 2021 | C17 |
| C4 | Clarke 2021 | C31 |
| C5 | Clarke 2021 | C52 |
| C6 | Clarke 2021 | C64 |
| C7 | Clarke 2021 | C67 |
| C8 | Clarke 2021 | C68 |
| C9 | Clarke 2021 | C71 |
| C10 | Clarke 2021 | C65 |
| C11 | Clarke 2021 | C127 |
| C12 | Clarke 2021 | C124 |
| C13 | Clarke 2021 | C128 |
| C14 | Nester 2024 | C12 |
| C15 | Nester 2024 | C7 |
| C16 | Nester 2024 | C16 |
| C17 | Nester 2024 | C22 |
| C18 | Nester 2024 | C46 |
| C19 | Nester 2024 | C53 |
| C20 | Nester 2024 | C52 |
| C21 | Nester 2024 | C70 |
| C22 | Nester 2024 | C58 |
| C23 | Nester 2024 | C61 |
| C24 | Nester 2024 | C89 |
| C25 | Nester 2024 | C60 |
| C26 | Blanco-Bercial 2026 | C6 |
| C27 | Blanco-Bercial 2026 | C7 |
| C28 | Blanco-Bercial 2026 | C14 |
| C29 | Blanco-Bercial 2026 | C15 |
| C30 | Blanco-Bercial 2026 | C21 |
| C31 | Blanco-Bercial 2026 | C22 |
| C32 | Blanco-Bercial 2026 | C23 |
| C33 | Blanco-Bercial 2026 | C25 |
| C34 | Blanco-Bercial 2026 | C26 |
| C35 | Blanco-Bercial 2026 | C31 |
| C36 | Blanco-Bercial 2026 | C46 |
| C37 | Blanco-Bercial 2026 | C48 |
| C38 | Blanco-Bercial 2026 | C51 |
| C39 | Blanco-Bercial 2026 | C53 |
| C40 | Blanco-Bercial 2026 | C50 |

## Second pass by reading (what would make each claim overstated?)

- **Clarke C1** is background about two *earlier* studies, so the caption says "Clarke's team note that two recent studies found ...". It is not Clarke et al.'s own result and is not used as a baseline against their 47.5%.
- **Clarke C3** includes "(which is not examined here)". The black box with a dashed arrow in B2.3 draws exactly that: the community at the site is not shown.
- **Clarke C5** says "approximately 40%" for both sample types; the bars (40, 40) are titled "approximately".
- **Clarke C6** is about the *top section* of cores at sites where both were collected (paired t-test, P = 0.67); the caption and the balance's pan label keep "top section".
- **Clarke C7 and C8**: the paper says "species" for 47/99; the Results elsewhere say "taxa" (see the earlier run's CLAIM-CHECK for the 99 "species" against "taxa" question). The comic uses C7's own words. The Discussion's "more than half the species ... detected in both" (page 39; private C93, `unverified`) is *not* used: it does not match the Results' 47/99 ("almost half").
- **Clarke C10**: replicate percentages are "based on the non-rarefied data"; kept in the caption. The paper notes one replicate pair was collected a day apart (private C25); not drawn.
- **Clarke C11**: "likely to reflect" and "demonstrating that ... do not necessarily reflect" are kept; the caption names the copepod as in the paper.
- **Nester C18, C19, C20**: the t, df and q = 0 details are dropped (listed in `left_out`); "Animalia" and "species richness" are the paper's words. C20: "arthropod (8 species) and chordate species (4 species)" is kept whole.
- **Nester C21**: the paper's own subset of paired samples ("merged eDNA samples", "paired CPR and merged eDNA samples at the same coordinates", private C67) is not drawn beyond the claim's wording.
- **Nester C22, C23** are the authors' own caveats and are drawn without softening. C23 compares open ocean with coastal environments, so it also shows why Clarke's nearshore result and Nester's open-ocean result are different tests.
- **Blanco-Bercial C30 to C32**: the paper says "69 of 100 samples remained after removal of contamination" under "amplification success". The chart title says "Samples remaining, of 100". The caption keeps the COI hedge about alternative protocols.
- **Blanco-Bercial C35** is the Discussion's own statement that clustering held "after removal of samples identified as contaminated based on taxonomic composition". It is drawn as a flow (samples, contaminated samples removed, clusters) so a reader does not take the clean clustering as the raw result. The comic does not say the removal was circular; the paper does not either.
- **Blanco-Bercial C36** draws two groups (V9 and V4 higher consistency; V1-V2 and COI higher variability) and not the Abstract's full ordering, which the body does not repeat (private C44, `abstract_only`).
- **Blanco-Bercial C38 (conclusion)** is the Conclusions' wording, not the abstract's stronger "accurate and valid descriptions ... throughout the ocean" (private C52, not used). It is introduced as the authors' conclusion and followed by their caveat (C39) and by C40.
- **Blanco-Bercial C40** (species not examined in detail) is drawn as a covered card, not as a missing result.

## Conflicts in the papers that the comic avoids (from the earlier runs)

- Clarke: Discussion (page 39) "more than half the species" against Results "almost half" (47/99): Results used. Abstract "99 metazoan species" against Results "99 taxa": the comic says "species" only inside C7/C8's own quoted sentence.
- Nester: Methods (page 6) say an accompanying R markdown file with code and data is available from the AAD Data Centre; the Data availability statement (page 13) says "Data will be made available on request": neither is used.
- Blanco-Bercial: the paper's page-53 sentence that COI shows similar patterns contradicts page 47 and page 56; the comic draws pages 47/56 only (C36). Mantel threshold written as "> 0.95%" is not used.

## Where the comic added its own wording

- **B1.4** (the overview of the three tests), **B5.1**'s side-by-side framing, Ines's lines ("So living things leave DNA behind, and we read it.", "So they went looking for animal DNA.", "Very different shares.", "Most. Not all."), Otto's question in B1.3 and the box labels are the comic's voice. None adds a number.
- **Two jokes, awaiting a human** (`keeps_claims_intact: false`): B4.2 (Otto: "I like my own protocol.") and B4.9 (Ines: "The closer you look, the less they agree.").
- **Ines and Otto** are invented. The cast `role` says so. Copepod in B2.9 and the people in B4.1/B4.10 are cartoon stand-ins.

## Checks run

`check_quotes.py --strict` on the ledger and the storyboard, `validate_storyboard.py --strict --variety`, `visual_qa.py`, and `strip_test.py` (3 panels flagged: see STRIP-TEST.md; none is a missing number the panel shows).
