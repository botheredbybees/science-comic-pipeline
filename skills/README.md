# Skills

Agent skills for the steps that need judgement. Each is a plain Markdown file (`SKILL.md`) with no
dependence on one vendor's tools, so any capable model can follow it; the mechanical steps are scripts,
so the skills stay short. Run them in this order.

| # | Skill | Does | Output | Scripts it uses |
|---|---|---|---|---|
| 1 | [`source-to-claims`](source-to-claims/SKILL.md) | Fetches the paper, checks its licence, lists what it claims with a verbatim quote and page for each | `claims.yaml`, `CLAIM-CHECK.md` | `fetch_source.py`, `check_quotes.py` |
| 2 | [`story-spine`](story-spine/SKILL.md) | Finds And / But / Therefore, chooses audience and cast, says what is left out, plans the beats | `head.yaml`, `PLAN.md` | |
| 3 | [`storyboard`](storyboard/SKILL.md) | Writes the panels, dialogue, captions and staging, citing a claim for every fact | `beats/B*.yaml`, `storyboard.yaml` | `build_storyboard.py`, `validate_storyboard.py`, `preview_storyboard.py` |
| 4 | [`humour-pass`](humour-pass/SKILL.md) | Proposes a few jokes that leave claims intact; flags each for a human | `humour` blocks | `validate_storyboard.py` |
| 5 | [`visual-qa`](visual-qa/SKILL.md) | Renders, scans for overflow and overlap, reviews every page by eye, fixes the staging | `QA.md`, the PDF | `visual_qa.py`, `export_pdf.py` |

**Commands.** The skills write `python scripts/...`; use the repo's own interpreter, `.venv/bin/python` (set up as
in the top-level README, so `jsonschema` and `pyyaml` are there). The pages are drawn in Patrick Hand, which the
sheet and the PDF export load from Google Fonts: they need a network connection, and an `.svg` opened on its own shows
a fallback font. Judge wrapping in the PDF, not in a bare SVG.

How they fit: the ledger (1) is the only place facts come from; the spine (2) decides the story; the
storyboard (3) is the product that renderers read; the humour (4) is optional; the QA (5) is the last look.

**The rule that holds it together:** nothing in a panel that is not in a cited, verified claim, and no joke
or caption that makes a claim say more than it does.

These skills were written from what two early comics (Lin 2017 and Akam 2026) needed, then followed cold by an agent that had
not seen those comics: first on Strzepek et al. 2022 (a perspective article with little story, 36 panels), then on
Pauli et al. 2021 (a primary research article, 46 panels), then on Lin et al. 2021 (a long data article, 59 panels), then on Xia et al. 2024 (an MDPI field survey, 52 panels, the first run to follow the HOWTO). Each
run finished a comic that passes the quote check, the validator and the scan, and each found real faults in the skills
and scripts, which were fixed before the next paper. The third run's were: bar labels that rounded `25.0` to `25`, prop
field names that were documented nowhere, a `wide` chart that could be packed at a third of a row, a locator separator
the checker rejected, a licence statement that was cut short, and unclear formats for `PLAN.md` and `ATTRIBUTION.md`.
The fourth run's were: a locator check that choked on headings with commas, authors and licence URL missing from MDPI's XML, an rRNA label counted as a number, speech lines doubled in the PDF's text layer, and a missing `ATTRIBUTION.md` template. Faults are getting smaller and rarer, but four runs are not proof: the next paper is the next test.
