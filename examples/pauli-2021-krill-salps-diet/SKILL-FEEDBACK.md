# Skill feedback: a cold run on Pauli et al. 2021 (primary research article)

Followed `skills/*/SKILL.md` in order. Result: 66-claim ledger (check_quotes --strict clean), 46 panels / 9 pages, validator clean except two jokes awaiting a human, scan clean, PDF exported. Nothing in scripts or renderers was changed.

## Cross-cutting

- **`python` is not on PATH here, and system `python3` lacks `jsonschema`.** Every skill writes `python scripts/...`; only the top-level README mentions `.venv/bin/python`. I used `.venv/bin/python` throughout. Change: say once in `skills/README.md` "use the repo's `.venv/bin/python` wherever a skill says `python`".
- **Patrick Hand is not installed** and no skill says how to install it (visual-qa: "should be installed or loaded"). The PDF and screenshots used fallback fonts, so wrapping was never checked with the real font. Change: ship the font (OFL) in `renderers/xkcd/fonts/` and embed it, or give the install command.

## 1. source-to-claims

- **"one paragraph or caption per file" is wrong.** Figure captions and flattened tables are glued onto the end of the preceding paragraph (p006 holds Table 1 as one run-on line, "Table 1Feeding modes and ..."; p010, p011, p012 end with a figure caption). A quote from a caption sits on the same "page" as the paragraph. Change: say so, and have `fetch_source.py` put captions and tables on their own pages.
- **No paragraph numbers in `page-map.txt`.** The schema wants `locator` ("Results, paragraph 2") but the map gives only section names, so I counted by hand and got most Discussion locators wrong (fixed afterwards). Change: print "para N of section" in `page-map.txt`.
- **Conflict handling covers only "caption versus body" ("A figure caption may contradict the body").** This paper contradicted itself in four ways the skill does not name: Results versus Discussion (26.5% vs "about one third"), a Discussion number borrowed from a different quantity (13.9% is dinoflagellates in the Results, used as "diatoms" in the Discussion), text versus Table 2 (p = 0.665 vs 0.661), and ANOSIM "significant differences between all sampling groups" vs "no significant difference between krill and salp diet". Change: add "cross-check every number and every 'no significant difference' in the Discussion and abstract against the Results and tables; record the conflict as `unverified`".
- **Abstract-sourced claims.** C58, C60, C61 are quoted from the abstract but restated in the body. The skill never says whether they are `verified` or `abstract_only`. I used `verified` with a note, because the body supports them. Change: say which.
- **Figures cannot be inspected on the Europe PMC path** (the XML has no images), yet the skill says "Note where the text and a figure disagree". Change: say how to get the figures, or say "if you cannot see them, say so in CLAIM-CHECK.md". I did not look at any figure.
- **"Aim for the paper's whole argument, not a sample" versus the storyboard skill's "Use each or drop it".** I wrote 81 claims, used 64, dropped 15 (deleted from the ledger) to satisfy "the ledger and the comic agree", then had two intentionally-unverified claims reported as "unused" on every build. Change: decide whether the ledger may exceed the comic; if yes, say unused claims are fine and let `build_storyboard.py` stay quiet about `unverified` ones.
- **Claim ids must match `^C[0-9]+$`**; only the schema says so.
- **`source.json` has `"year": "2021"` (string)**; the schema wants an integer. The story-spine skeleton warns ("an integer, not a string") but source-to-claims, which tells you to copy from `source.json`, does not.
- **Rule "must not start or end on a word with a digit stuck to it" is not checked by any script**, so I could not tell whether I obeyed it.
- Worked well: the licence gate, the quote check (it caught nothing because I copied from the page files, which is the point), the "what would make this overstated?" second pass (I reworded three claims after it).

## 2. story-spine

- **No salp body.** `body` offers diatom, krill, penguin, whale; the paper is about a salp. I drew Sal as a plain stick figure and said so in the cast and CLAIM-CHECK.md, but the picture teaches nothing about what a salp is. Change: add a salp body, or say in the skill that a missing body should be a stick stand-in with a caption.
- **`extra` cannot carry a body.** The skill says "others are props or `extra`", but a whale and a penguin in one panel had to be full cast entries (five cast, against "three or four recurring").
- **A general audience needs definitions the paper does not give.** "Syndiniales", "Prymnesiophyceae", "Ivlev's index", "Filosa-Thecofilosea" are used in captions with only the paper's own gloss ("parasitic dinoflagellate group"). The skill says "explain a term once in a caption" but the rule that nothing may be added beyond claims means the comic cannot explain them. Change: say what to do (use the paper's gloss, or label the term as "a group of plankton" only if a claim supports it, or accept jargon and list it in `left_out`).
- **It does not say whether claim ids may appear inside `meta.spine` text.** I included them; nothing complained. Say so.
- **No guidance on panel count versus claim count.** "No limit" produced 46 panels for one paper; the story still holds, but a rule of thumb (about one claim per panel, 30 to 50 panels) would help.
- **The skill's "little conflict" paragraph was useful.** I used it to avoid inventing a villain ("the tension is the overturned assumption").

## 3. storyboard

- **Krill scale "1.3 to 1.5" collides with neighbours.** At 1.4 a krill is about a third of a standard panel's width and overlapped Sal and the bowl. I used 1.0 to 1.2. Change: say "1.0 to 1.2 beside others; 1.3 to 1.5 alone".
- **`title` on a `bars` prop is accepted by the schema and counted by the validator but not drawn.** Seven charts had no title until I added `label` props. Change: draw it (a renderer fix) or document it in `renderers/README.md`.
- **`bars` cannot show negative values**, and nothing in the skill says how to draw a signed index. I used an `axis` with `mark` items at (value+1)/2 positions. Change: say so in the skill or add signed bars.
- **A tick number such as "0" on an axis triggers "number appears on the panel but in none of its cited claims".** I cited the claim that defines the scale (C31) to clear it. Say that axis ticks count as numbers.
- **`scene` is "alt text" but nothing checks it against staging**; I caught two errors only by re-reading (B1.8 said "board", none staged). A cheap script check ("every noun in `scene` that is a prop kind must be staged") would help.
- **`height: tall` on an axis panel does not help**: it only adds empty space above a thin axis (B4.1 to B4.3). The advice "tall for a significant beat" works for people and bar charts, not for axes.
- **Unused-claim reporting** (see source-to-claims).
- **Caption length rule (12 to 35 words) versus long claims**: several claims run 30 to 40 words, so I shortened them. "A caption may shorten a claim, never strengthen it" does not say what is safe to cut when the hedge is in the middle. An example would help.
- **No instructions for viewing the HTML preview in a headless setting.** I generated it but read the story from the rendered pages instead.
- Worked well: the validator's "invented number" check, the hedge/scope reminder, `build_storyboard.py` reporting uncited claims.

## 4. humour-pass

- **A joke on a panel with no `claim_ids` is never flagged** (the validator only warns when claims are cited). All panels here cite claims, but the skill promises that the warning "is the flag", which is not true for a claim-free panel.
- **The five questions are good but long**; writing them into `humour.note` made 100-word notes. Suggest a shorter template ("1 no / 2 ... / 3 ...").
- **Does a face count as a joke?** Kip and Sal smiled in B4.5 for tone. I removed Kip's smile and treated Sal's as part of the joke. The skill is silent on faces and poses as humour.
- The "at most one per beat, fewer is better" guidance was right: two jokes (B4.5, B6.1) were enough; both left `false`.
- Expected result achieved: `validate --strict` shows exactly one warning per joke and exits 1; the skill should say that exit 1 is the right end state here.

## 5. visual-qa

- **Crowded axis labels: the table's "row on an axis" does not work for clustered marks.** Lift is relative to each label's own height, so labels of different heights overlap, and leader lines cross lower labels. The scan flagged it; the fix that worked was one combined label per cluster. Change: add that to the table.
- **The checklist does not mention chart titles** (see above); I only caught them because I looked.
- **The scan cannot see a leader line crossing text, or text touching the top of a solid bar** (value labels overlap tall solid bars slightly, left as is).
- **Attribution on the last page omits the licence URL**, which CC BY asks for; "Check ... that the attribution is printed" should say what a complete one contains. The PDF `Title` metadata ends with "xkcd Pages".
- **Nothing says to compare the PDF with the SVG.** I did a low-resolution contact sheet; layout matched.
- **Blank band fix**: "height: tall on a significant panel" worked for the ship panel (p2) but is a trial and error loop; the layout re-packs, so a fix on one page can move content on the next.
- Worked well: the headless Chrome screenshot recipe, the two-step "scan, then look", and "do not stop at the first clean scan" (the first scan was clean, and I still fixed eight things by looking).

## Top defects, in order of cost

1. `title` on `bars` silently not drawn, and no signed-value chart (affects every data paper).
2. Conflicts inside the paper (Results vs Discussion, text vs table) are not covered by the skill's "caption versus body" rule; the quote checker cannot find them.
3. Page files merge captions and tables into paragraphs, and `page-map.txt` gives no paragraph numbers, so locators are hand-counted.
4. `python` / venv and the Patrick Hand font are unmentioned in the skills.
5. "Use each claim or drop it" versus "aim for the whole argument": unclear whether to delete unused or `unverified` claims; and no salp body / `extra` bodies for the cast.

## What was done about it (2026-11-13, after this run)

- `bars` draws its `title`, stands bars on a zero line and draws negative values (`min: -1`); documented in `renderers/README.md` and the storyboard skill.
- A `salp` body, and a `body` on a staged character so an `extra` can be an animal; Sal is now a salp.
- `fetch_source.py` gives figure captions and tables their own pages and `page-map.txt` numbers paragraphs within a section path;
  `check_quotes.py` warns when a `locator` disagrees with the map. The pages of this paper and of Strzepek were re-fetched and every claim's page remapped.
- `source-to-claims` names the four kinds of conflict inside a paper, says abstract claims the body restates are `verified`, says the ledger may exceed the comic,
  and how to say the figures were not seen. `build_storyboard.py` lists only verified unused claims, as a prompt.
- The validator warns on a joke with no cited claim, and on a scene that names a prop that is not staged (it found four real alt-text defects in the three comics, now fixed).
- The last page's attribution gives the licence URL; the PDF title no longer ends in "xkcd Pages".
- `skills/README.md` says to use `.venv/bin/python` and that the font comes from Google Fonts, so judge wrapping in the PDF.
- Not done: a `scene`-against-staging check beyond the prop words; the scan still cannot see a leader line crossing text.
