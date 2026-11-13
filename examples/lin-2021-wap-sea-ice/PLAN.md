# Plan: Lin et al. 2021, plankton diversity and carbon flux at the Western Antarctic Peninsula

Slug `lin-2021-wap-sea-ice`. Ledger: `claims.yaml` (76 claims, 74 verified, 2 unverified: C25, C37). Written 2026-11-13.

## Audience

Marine science students and curious readers who know that Antarctic sea ice is shrinking but have not wondered
what that does to the plankton, or to the carbon they move. A term is explained once, in a caption, with the
paper's own gloss (NCP C6, WGCNA C20, module C21, GP C23, ASV in C15). Terms the paper does not gloss (CCA, Chao1,
DIC) are kept as the paper's words and, for DIC, left out.

## Spine (also in `head.yaml`)

- **And:** the Western Antarctic Peninsula has the fastest sea ice decrease in Antarctica (C3); its plankton support
  krill, penguins and whales (C4); NCP reflects the organic carbon available for export (C7).
- **But:** it is imperative to understand how plankton community, biodiversity and carbon flux will change (C5).
  And the five years studied were a period of moderately positive ice anomalies, not record-low ice (C32): the paper
  reads the decline from year-to-year differences, not from a trend. (The abstract's "remain an open question" is
  not restated in the body, so it is not used.)
- **Therefore:** five years of NCP plus 18S DNA (C10); diatoms 39.5% of reads in late-retreat years against 14.0% in
  early-retreat years (C35, C36); richness, evenness and Shannon fall with SST (C42, C43); a diatom-and-dinoflagellate
  module (MET) is the best community predictor of NCP (C54, C57); the authors hypothesise three patterns (C70 to C74);
  a longer time series is needed (C80).

## Cast

Wren (guide, long light hair, glasses, lab coat, clipboard); Teo (sceptic, woolly hat, mug of tea); Dot (a diatom); Kip
(a krill, one appearance with a role in the hypothesis). Penguin and whale are `extra` bodies in one panel. Cryptophytes,
dinoflagellates and haptophytes have no body in the renderer, so they appear only in charts, labels and cards.

## Beats

| beat | job | claim ids | weight and rhythm |
|---|---|---|---|
| B1 Problem: the fastest-changing coast (6 panels) | the world, what plankton do, what NCP is, the but | C2 C3 C4 C6 C7 C5 | wide opener, small asides, wide quiet panel for the "imperative" line |
| B2 Method: five Januaries at sea (8) | ship, filter, freeze, 18S, ASVs, O2/Ar, the mixed-layer caveat | C11 C10 C32 C12 C13 C14 C15 C16 C17 C19 | alternating standard and small, a flow strip for the pipeline |
| B3 Result: who turns up in which year (9) | NCP by place and year, the study-years caveat, community shares, the high-ice against warm-year bars, CCA | C30 C31 C39 C32 C33 C34 C35 C36 C38 C40 C41 | charts are the point: full-width paired bar chart; wide quiet panel to close |
| B4 Result: warmer water, less diversity (8) | richness, evenness, Shannon fall with SST; Tara Oceans goes the other way; explanation; the authors' hedged line | C42 C43 C45 C44 C46 C48 C47 C49 | full panel for the schematic plot; full quiet panel to close |
| B5 Result: which community predicts the carbon (17) | ASVs too many, WGCNA, modules, GP, fit, physical factors, MET, its members, its correlations, MER and MEG | C27 C20 C21 C22 C15 C23 C24 C50 C51 C7 C52 C54 C55 C56 C57 C59 C58 C60 C61 C64 C65 C66 | the longest beat: signed and plain bar charts; board for the genera |
| B6 Discussion: three patterns, and what the authors cannot say (11) | hypotheses i, ii, iii, projection, caveats (iron, snapshots, validation, proxy), longer series | C70 C71 C72 C73 C74 C75 C76 C62 C63 C77 C78 C79 C80 | caveats near the claims they qualify; closing panel full and quiet |

59 panels, 11 A4 pages.

## Left out (see `meta.left_out`)

Figures (only text read); supplementary figures and tables; batch-correction methods (QMP); sequencing and DADA2
details; module-trait statistics beyond a few correlations; the Southern Annular Mode paragraph; DIC check;
filter pore size change; the Southern Ocean's share of CO2 and heat uptake (C1); previous work on ice-melt stability
(C9); the internal conflicts of the paper (CLAIM-CHECK.md).

## Verified claims that no panel cites

C1, C8, C9, C18, C26, C53, C81 (the builder lists them). All checked and left out on purpose: they are background or
detail the story did not need. C25 and C37 are `unverified` and never drawn.

## Jokes

Three at most, one per beat at most: B2.3 (Teo's tea against a -80 degrees C filter; checked, `true`), B4.7 (Dot smug about
diversity; left `false`), B6.11 (Teo's tea callback beside the longer-series caveat; left `false`). See `QA.md`
and the humour notes in `beats/`.
