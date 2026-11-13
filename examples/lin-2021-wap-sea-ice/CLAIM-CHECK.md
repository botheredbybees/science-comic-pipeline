# Claim check: Lin et al. 2021, Nature Communications

**Date:** 2026-11-13.

**Source:** Lin Y, Moreno C, Marchetti A, Ducklow H, Schofield O, Delage E, Meredith M, Li Z, Eveillard D, Chaffron S,
Cassar N. *Decline in plankton diversity and carbon flux with reduced sea ice extent along the Western Antarctic
Peninsula.* Nat Commun (2021), DOI 10.1038/s41467-021-25235-w, PMC8368043. Fetched with
`scripts/fetch_source.py --doi 10.1038/s41467-021-25235-w -o sources/lin-2021-wap-sea-ice` (exit 0, 40 numbered pages).

**Licence:** CC BY 4.0. The fetch script's gate passed, and the licence statement is in the article's own XML
(`<license>`): "This article is licensed under a Creative Commons Attribution 4.0 International License, which permits use,
sharing, adaptation, distribution and reproduction in any medium or format, as long as you give appropriate credit to the
original author(s) and the source, provide a link to the Creative Commons license, and indicate if changes were made."
Third-party material is covered unless a credit line says otherwise; the comic uses none of the article's images.

**What was read:** every page file `p001` to `p040`, including captions and Methods. Europe PMC's XML has no images, so
the figures (Figs. 1 to 5) and the supplementary material (Figs. S1 to S6, Table S2, Supplementary Data) were not seen.
Anything only a figure shows is not in the ledger.

**Script results:** `check_quotes.py examples/lin-2021-wap-sea-ice/claims.yaml --pages-dir sources/lin-2021-wap-sea-ice/pages --strict`:
76 claims checked, 0 errors, 0 warnings (exit 0). 74 verified, 2 unverified (C25, C37). Second pass by reading: each
claim was read against its quote. Claims that were weakened or annotated during that pass: C1 (the sentence does not say
"CO2 uptake"), C2 and C3 (split, so each quote is contiguous), C15 (sample count disputed, below), C32 (study years,
quote widened to include "2012 to 2016"), C74 (hypothesis).

## Conflicts and oddities in the paper

The checker cannot find these; they were found by reading. The comic follows the first (Results) version and draws none of
the others.

1. **Number of samples.** 119 samples (Results, paragraph 3, p010; claim C15) against "after discarding two samples ...
   the libraries (n = 117)" (Alpha diversity, p030) against 112 samples in the WGCNA run (p037) and in the GP dataset
   (p038; claim C26). The comic draws "2480 ASVs" and never a sample count.
2. **Number of physical factors.** "physical factors (n = 6)" (Results, paragraph 5, p014; claim C25, `unverified`) against
   nine named in Methods (MLD, PAR, PAR_mld, Salinity, SST, fsim, fmet, X grid, Y grid; p038). Not drawn.
3. **A doubtful significance claim.** "all significantly different from cold years (two-sided t-test, p < 0.0001)" (p009;
   claim C37, `unverified`). Diatoms, cryptophytes and haptophytes differ clearly (39.5 against 14.0; 15.1 against 28.9;
   7.1 against 14.4), but dinoflagellates are 20.5 +/- 1.3 against 19.0 +/- 1.6, and no sample sizes are given. Not drawn;
   the chart shows the means only and the caption does not use the word "significantly".
4. **"High sea ice" against "late retreat".** The Results call 2014 and 2016 "late sea-ice retreat" (p007) and then "high
   sea ice" (p009); 2012, 2013 and 2015 are "early" (p010) or "warm years with less sea ice" (p009). The abstract speaks of
   "lower sea ice extent". The comic uses the paper's own words where each appears (C31, C35, C36, C39) and does not equate them.
5. **Study years were not low-ice years.** p007: 2012 to 2016 "was a period of moderately positive sea-ice area anomalies
   following a more prolonged period of anomalously low SIA". The title and abstract speak of a "decline ... with reduced
   sea ice extent", but what the data show is a difference between years, and the authors say a longer time series is
   needed (p019). The comic shows C32 (caveat) and C79/C80 near the conclusion, and never says plankton "have declined".
6. **"Dominant" in the abstract against the body.** Abstract: sea-ice extent "is a dominant factor". p010: "either ice
   conditions or SST is the dominant driver". The comic quotes the body (C38) and leaves the either/or visible.
7. **"Less than 5%".** "Other eukaryotic plankton groups ... contributed less than 5% of the 18S reads" (p009; C34), but the
   four main groups sum to 78.9%, so the others together are about 21%: the sentence can only mean each group. Cited only to
   name the unit (reads); the "5" is never drawn.
8. **Time span.** The first abstract says "since the middle of the past century"; the second abstract paragraph says "over the
   past century" (p001, p002). The comic uses the Introduction's "up to 7 degrees C since 1950" (C2).
9. **Two different "0.7"s.** R2 = 0.70 for GP solution 1 (p015; C57) and R = 0.7 for module membership against volumetric NCP
   (Fig. 5 caption, p016). Different quantities; only the first is used. Whether the R2 values are on the training or the
   validation half is not said (p038 says the data were split in two).
10. **Methods oddity, not drawn.** p035 relates cryptophyte alloxanthin to cryptophyte 18S counts and then checks the result
   against *Phaeocystis* CHEMTAX abundances (Phaeocystis is a haptophyte); possibly a mislabel. Not used.
11. **A filter change, not discussed.** 0.45 um filters in 2012 and 2013, 0.2 um in 2014 to 2016 (p023; C12). The paper does not
   say whether this affects the comparison between years. Left out of the comic (in `left_out`).
12. **Sanity check on the percentages (my arithmetic, not the paper's).** Weighting the two-year and three-year means 2:3
   gives diatoms 24.2%, cryptophytes 23.4%, dinoflagellates 19.6%, haptophytes 11.5%, against the paper's overall 25.0, 23.0,
   19.6, 11.3. Close enough to suggest the shares are internally consistent.
13. **Ambiguous sentence (C1).** "almost half of the anthropogenic CO2 and 75% of the heat uptake by the oceans": the verb is
   shared, and the comic does not use the sentence.

## Where the comic adds its own voice (not claims)

Wren and Teo's questions and replies ("Ice or temperature, then?", "The paper says either.", "After a long run of low ice. Keep
that in mind.", "So it is a mixed-layer measurement.", "Diatoms again."), the chart titles, and three jokes (Teo's tea
in B2.3 and B6.11, Dot's "Just saying" in B4.7). The schematic plot in B4.1 is labelled "schematic": its line is not data, and
its only numbers (40%, 4 degrees C) are the paper's. Bar values come from C33, C35, C36, C59 and C60. A bar chart's axis maximum
is hidden (max 45 for percentages, 1 for correlations), so no uncited scale number is drawn.

## Doubts left for a reviewer

- The percentages in C33 are attached to "18S reads" through the next sentence (C34); C33 itself says only "dominated".
- In the correlation chart (B5.13) the bar "SST -0.51" is the paper's "low SST (R = -0.51)": a negative R with SST.
- Chart values are printed by the renderer with `%g`, so 25.0, 23.0, 14.0 and 19.0 appear as 25%, 23%, 14% and 19%; the
  captions carry the paper's exact figures (25.0%, 23.0%, 14.0 +/- 1.7%).
- The schematic line in B4.1 has an arbitrary slope; the "40% lower for a 4 degrees C rise" note is the paper's.
