# Claim check: *Specific eukaryotic plankton are good predictors of net community production in the Western Antarctic Peninsula*

Checked on 2026-11-13 against the full text (Europe PMC PMC5665988), which was split into 28
paragraph-level pages.

## Result

All 66 claims in `claims.yaml` carry a verbatim quote and the page (paragraph) it was taken from.
`scripts/check_quotes.py` confirms each quote is on its page, with 0 errors and 0 warnings. Of those,
all 66 are used in the storyboard. `scripts/validate_storyboard.py --strict` also confirms that every
number drawn on a panel comes from one of its cited claims.

Two checks caught real slips of our own while this was built:

- A quote dropped a word ("organic matter production"), found by the quote checker and corrected.
- A pie chart labelled "all the rest: 22%". That figure is 100 minus 78 and is not in the paper. The
  number check found it and the label was changed to "everything else".

## Things in the paper worth knowing

- The Figure 4 caption says edges are "strong and significant connections (SparCC correlations with
  magnitude > 0.75 and p-values > 0.05)". Significance would normally be p below 0.05, so this looks like
  a typo. The comic does not use it.
- The Results sections lack headings in the full-text copy, so locators say "Results, paragraph N".
- The paper calls its test a "good predictor" on the basis of variance explained among 21 stations, with
  11 stations in each network group (C50), so the comic keeps the paper's own caveats (C50, C55 to C57).
- The paper does not mention fluorescence instruments. The cross-reference to a fluorescence flash in
  the last beat is the comic's joke, and the paper's actual wording is its call to validate with
  "photophysiology" (C58).

## Method

Text read from the Europe PMC full-text XML. Footnote numbers are printed attached to words in this
journal's text ("density1"), so a quote cannot end on such a word; this is why some quotes stop early. The
full text is not stored in this repository.
