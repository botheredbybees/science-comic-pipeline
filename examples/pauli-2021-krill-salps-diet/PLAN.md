# Plan: Who Eats What? (Pauli et al. 2021)

Source: Pauli et al. 2021, *Communications Biology*, doi 10.1038/s42003-021-02581-5 (CC BY 4.0).
Slug `pauli-2021-krill-salps-diet`. Ledger: `claims.yaml` (81 claims; C80 and C81 are `unverified` on purpose).

**Audience.** Curious adults with no biology background who know krill and penguins but not salps.

**Spine (And / But / Therefore).**
- And: krill and salps are two dominant Southern Ocean grazers; krill are known selective feeders, salps are assumed to be indiscriminate; warming is making their ranges overlap (C1, C8, C10, C11).
- But: nobody had compared their diets side by side in the same place with the same method (C9, C15).
- Therefore: sequence stomach contents, fecal pellets and the plankton along the Peninsula (autumn 2018) and add fatty acids. Neither diet matched the plankton, so salps look selective too, and the two diets are broadly similar (C58, C60, C62).

**Honest-story note.** This is a primary research article with a real, mildly surprising result ("salps are not indiscriminate") but little conflict. The tension is the overturned assumption; there is no villain and none is invented. The "competition" claim stays at the abstract's hedge ("potentially enhancing").

**Cast.** Mara (guide, scientist on the ship), Kip (krill), Sal (salp, a plain stick stand-in because the renderer has no salp body), Whale and Penguin (one panel each, as krill predators). Everything else is `extra`.

**Left out.** See `left_out` in `head.yaml`.

## Beat table

| beat | act | job | claim ids | weight and rhythm |
|---|---|---|---|---|
| B1 Two grazers | problem | Introduce krill and salps, the overlap, the untested assumption | C1 C2 C3 C5 C6 C7 C8 C10 C11 C15 | wide opener, small quick beats, a chart-like axis for the 60 to 65 °S shift, a wide pause on the assumption, the "but" panel last |
| B2 What did they eat? | method | Cruise, nets, three kinds of sample, metabarcoding in one panel, the predator-DNA problem, fatty acids | C16 C17 C18 C19 C20 C21 C22 C23 C24 C25 C26 C27 C30 | full-width ship opener; sample-count bars as the chart; a small panel for controls |
| B3 The menu | result | Plankton versus krill and salp stomachs, as charts; the Syndiniales surprise and its caveat | C33-C45 C73 C74 | three wide bar-chart panels (the data is the point), then two quick panels |
| B4 Picky eaters | result | Ivlev index explained once, then each animal's likes and dislikes; the headline | C31 C48-C52 C58 C59 C62 | wide axis panels, payoff panel (the abstract's sentence) as `full` |
| B5 After the meal | result | Fatty acids; fecal pellets; salps eating krill pellets; krill meeting salps | C30 C53 C54 C55 C66 C67 C68 C69 C40 C70 C71 C72 | one chart of fatty acids, then conversational panels; the caveat "not seen feeding directly" lands next to the claim |
| B6 So what? | discussion | Back-flushing as a possible mechanism; similar diets and competition; the plankton-shift implication; caveats and what next | C60 C61 C14 C63 C64 C65 C75 C32 C77 C78 C76 | wide quiet panel for the unknown; caveats near the claims they qualify; last panel is the authors' own call for more tests |

## Checks planned

- Charts only show values that are in cited claims. The Ivlev chart places marks at (value+1)/2 on a -1..+1 axis.
- Unverified claims C80 and C81 are not drawn (internal contradictions in the paper; see CLAIM-CHECK.md).
- Jokes at most three; each left `keeps_claims_intact: false` unless clearly safe.
