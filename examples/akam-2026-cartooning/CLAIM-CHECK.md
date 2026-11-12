# Claim check: *Cartooning in Biological Learning*

Checked on 2026-11-13 against the full text (Europe PMC PMC13022473) and Figures 3 to 7
(images from the PMC page). The paper is CC BY 4.0. This file is our record and is not
endorsed by the authors. Nothing below has been put to the authors.

## Result

All 15 claims in `storyboard.yaml` are marked `verified`. The first draft rested on the
abstract alone. Eight of its nine claims had to be reworded, split or corrected, because the
full text and figures differ from the abstract in places. Only the 68% preference figure
survived unchanged.

## Differences between the abstract, the text and the figures

| # | What the abstract or text says | What the figures show | What the storyboard uses |
|---|---|---|---|
| 1 | The abstract says there was a "significant statistical difference" in quiz performance and gives no direction. | Figure 7: cartooned subtopics (solid bars, Q5 to Q10) scored higher than not-cartooned (patterned bars, Q1 to Q4). | Cartooned higher, with medians 81.74 and 50.55 (C10). |
| 2 | Results: "median (IQR) 50.55 (31.69) vs. 81.74 (19.32), respectively", in a sentence that names cartooned first and non-cartooned second, which reads as cartooned lower. | A median recomputed from the bars in Figure 7 gives about 81.5 for cartooned and about 50 for not-cartooned. | The figure's direction. The text's order looks like a slip. |
| 3 | The abstract gives "engagement 4.8, learning 4.5, understanding 4.2". | Figure 3: 4.8 is "well organised, instructions clear". Figure 4: engagement is 4.5. Figure 5: learned about own group's topic 4.5; improved understanding 4.2. | Each rating labelled by its survey item (C12). |
| 4 | Results, Engagement: "60% and 30% of students gave a score of four and five". | Figure 4: 5 is about 60% and 4 about 30%, and the average is 4.5. | Average only, not the split. |
| 5 | Not in the abstract. | Figure 5: learning about other groups' topics rated 3.3, with 42% neutral. | Included, as a counterweight (C12). |
| 6 | The Discussion and Conclusion do not mention the quiz comparison. They rest the case on the survey and the free-form comments. | | The quiz result is reported, with its caveat (C11). |

Smaller points: the abstract's "fostered teamwork among cohorts" is a theme in 120
free-form comments (collaborative learning, 30% of responses), not a measured outcome
(C15). The Discussion cites "Figure 9" for the "Ouch" exonuclease cartoon, but Figure 9
is the theme-frequency graph and that cartoon is Figure 10.

## Limits worth keeping in the comic

- The quiz comparison has 20 observations, which are question-level averages from two
  modules, with six cartooned and four not-cartooned questions (C11). The paper says the
  Part A and Part B modules each gave a quiz and reports no quiz for Part C.
- Only 44% would consider cartooning for revision and 20% scored 1 or 2 (C14).
- Learning from other groups' cartoons was rated 3.3 (C12).

## Method

Text read from the Europe PMC full-text XML; figure values read by eye from the PMC
images, and the medians recomputed from the Figure 7 bars to test the label order. The
bar readings are approximate (about 2 percentage points). The full text and images are not
stored in this repository.
