# Skills

Agent skills for the steps that need judgement. None is written yet. The mechanical
steps (validation, rendering, screenshots) are scripts, so the skills stay short.

| Skill | Does | Output |
|---|---|---|
| `source-to-claims` | Reads the paper, lists what it claims, cites a locator for each, marks each `verified` only after checking the full text | the `claims` ledger |
| `story-spine` | Reduces the paper to And / But / Therefore, picks a cast, and proposes a page plan | `meta.spine`, `cast`, `pages` skeleton |
| `storyboard` | Writes the panels, dialogue and captions, citing a claim for every fact | `storyboard.yaml` |
| `humour-pass` | Proposes jokes that leave claims intact; flags each one for review | `humour` blocks |
| `visual-qa` | Renders, screenshots, and checks for overflow, overlaps and unreadable text | a list of defects |

Each skill must work with any capable model, so the instructions live in plain
Markdown and nothing depends on one vendor's tool names.
