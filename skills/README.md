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

How they fit: the ledger (1) is the only place facts come from; the spine (2) decides the story; the
storyboard (3) is the product that renderers read; the humour (4) is optional; the QA (5) is the last look.

**The rule that holds it together:** nothing in a panel that is not in a cited, verified claim, and no joke
or caption that makes a claim say more than it does.

These skills were written from what the Lin 2017 and Akam 2026 examples needed. They have not yet been tested
by someone who has not seen those examples; the first test is to follow them cold on a new paper, and
what goes wrong there is recorded in the design document.
