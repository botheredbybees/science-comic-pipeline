# science-comic-pipeline

Turn a scientific paper into a short comic that stays true to the paper.

Papers and data products reach few people if they only exist as papers. This repo is a
repeatable process for the middle step: **read the paper, pull out what it actually
claims, find the story in it, and hand a structured storyboard to a renderer.**

> **Status: working, still early.** Five papers have been turned into comics; two are kept here as examples (the PDFs are below), the storyboard
> schema, validator and renderer are tested, and five skills describe the judgement steps. Three of the comics were made
> by an agent that had only the skills to go on, which is how the skills were debugged. See
> [the design](docs/superpowers/specs/2026-11-13-science-comic-pipeline-design.md).

## Examples

Each comic is a finished A4 PDF kept beside its storyboard, claims ledger and attribution. Every comic carries its
source paper's licence, a link to the paper, and the line that its authors did not write or endorse it.

| Comic | Paper | Pages |
|---|---|---|
| [Who Eats What?](examples/pauli-2021-krill-salps-diet/pauli-2021-krill-salps-diet.pdf) | Pauli et al. 2021, *Communications Biology*: what krill and salps eat, read from their DNA | 9 |
| [Draw It Yourself](examples/akam-2026-cartooning/akam-2026-cartooning.pdf) | Bahsoun, Morris and Akam 2026, *Biochemistry and Molecular Biology Education*: learning biology by drawing cartoons (a draft) | 2 |

## The idea

```
paper ──> claims ledger ──> story spine ──> storyboard.yaml ──> renderer ──> pages
          (cites the        (And / But /     (validated)        (xkcd-style,
           paper)            Therefore)                          painted, ...)
```

- **Every fact in a panel cites a claim, and every claim cites the paper.** The
  validator refuses a panel with a number in it and no claim behind it, and warns
  when a claim has only been checked against the abstract.
- **The storyboard says what happens and how much room each moment gets, not how it is laid out.** Panels have a weight (small, standard, wide, full), as in a printed comic, and carry Scott McCloud's panel-to-panel transitions and word-and-picture modes.
- **The storyboard is the product.** Renderers read it and never the paper, so a new
  drawing style is a new renderer and nothing else.
- **Humour is optional and flagged.** A joke on a panel that cites a claim needs a
  reviewer to confirm it leaves the claim intact.

## Make a comic

The full guide, with set-up for Claude Code, Codex, Gemini CLI, Cursor, Copilot and others, a prompt to paste, and
troubleshooting, is [HOWTO.md](HOWTO.md). The short version:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/fetch_source.py --doi <doi> -o sources/<slug>            # the paper's text, and its licence check
# then the five skills in skills/, in order, which write examples/<slug>/ ...
.venv/bin/python scripts/build_storyboard.py examples/<slug>                       # head + beats + claims -> storyboard.yaml
.venv/bin/python scripts/validate_storyboard.py examples/<slug>/storyboard.yaml --strict
.venv/bin/python scripts/visual_qa.py examples/<slug>/storyboard.yaml --keep output/<slug>
.venv/bin/python scripts/export_pdf.py examples/<slug>/storyboard.yaml -o examples/<slug>/<slug>.pdf
```

**Which steps need a model?** Only the judgement steps: choosing the claims, finding the story, writing the panels and
staging, proposing jokes, and looking at the pages. Everything else is a plain script, and that includes the PDF:
`export_pdf.py` draws the pages itself (SVG, with the wobble seeded, so the output is identical on every run) and prints
them with a headless Chrome or Chromium. No image model is involved anywhere, so a number in a chart is always the number
in the claim behind it. `pytest tests` runs the tests.

To try the renderer on an existing storyboard without making anything:
`.venv/bin/python renderers/xkcd/render.py examples/akam-2026-cartooning/storyboard.yaml -o output/xkcd`.

The Akam example is a draft storyboard of an open-access paper about students learning
biology by drawing cartoons. All its claims were checked against the full text and
figures, and [CLAIM-CHECK.md](examples/akam-2026-cartooning/CLAIM-CHECK.md) records what
that turned up (the abstract and the paper's own text disagree with its figures in
several places). Set a claim's `status` to `abstract_only` and the validator warns.

## Layout

| Path | What it is |
|---|---|
| `schema/storyboard.schema.json` | The storyboard format (JSON Schema): beats of panels, each with a weight, an optional transition and word-picture mode |
| `scripts/validate_storyboard.py` | Schema check plus the accuracy-ledger rules; no limit on panel count |
| `scripts/fetch_source.py` | Fetches an open-access paper from Europe PMC, checks the licence, splits the text into numbered pages |
| `scripts/visual_qa.py` | Renders a storyboard and scans the pages for overflowing or overlapping text |
| `scripts/check_quotes.py` | Confirms every verified claim's quote is on the page it names in the source |
| `scripts/build_storyboard.py` | Assembles a storyboard from a working folder (head, beats, claims) |
| `scripts/export_pdf.py` | Exports a storyboard as a PDF, one A4 page per comic page (needs Chrome or Chromium) |
| `scripts/layout.py` | Packs panels into rows, left to right then down: no blanks, at most 3 across, looks ahead |
| `scripts/preview_storyboard.py` | A readable page: sideways strip, printed rows or vertical stack |
| `examples/` | Example papers, each with its licence record, claims ledger, storyboard and claim check |
| `renderers/` | One folder per drawing style. `xkcd/` draws stick-figure A4 pages from a panel's `staging` |
| `HOWTO.md`, `AGENTS.md` | How to run it end to end in your AI environment; the briefing every agent reads first |
| `skills/` | Five agent skills for the judgement steps, in order: source-to-claims, story-spine, storyboard, humour-pass, visual-qa |
| `docs/superpowers/` | Design and plans |

## Licences

- **Code and schema:** [MIT](LICENSE).
- **Docs, and the example outputs:** [CC BY 4.0](LICENSE-CONTENT-CC-BY-4.0.txt) where the example's own source is CC BY.
  A comic adapted from a source inherits that source's licence: an adaptation of a ShareAlike
  source (CC BY-SA) must be released under the same licence, not under plain CC BY.
- **Source papers are not copied here.** Only papers with a licence that allows
  adaptation (CC BY, CC BY-SA or CC0) are used as examples, and each records where and when
  the licence was checked. See [ATTRIBUTION.md](ATTRIBUTION.md).

If you adapt a paper under a licence with a NoDerivatives clause, you cannot share the
result. Check the licence before you start.
