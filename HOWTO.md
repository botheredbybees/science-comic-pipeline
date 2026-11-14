# How to make a comic from a paper

This is the whole process, from an empty machine to a PDF, using an AI coding agent for the judgement steps. If you only
want to look at what the pipeline makes, open one of the PDFs in [examples/](examples/).

**What happens.** An agent reads an open-access paper and writes a *claims ledger* (every statement the comic may rely
on, each with a word-for-word quote and its page). It then finds the story, writes a *storyboard* in which every number
cites a claim, adds a few flagged jokes, and checks the pages. Scripts do everything mechanical, including drawing and
exporting the PDF. No image model is involved; the pictures are drawn from the storyboard by the renderer. A human reads
the result before it goes anywhere.

A full run on a 10-page article has taken an agent about 15 minutes and 300,000 tokens, and produces 35 to 60 panels.

## 1. What you need

| | |
|---|---|
| **Python 3.10 or newer**, and `git` | the scripts and tests |
| **Chrome or Chromium** | exports the PDF (headless; the scripts look for `google-chrome`, `chromium` and similar on your path) |
| **`curl`** | fetches papers from Europe PMC (or save the paper's XML yourself and use `--xml`) |
| **An internet connection** | for Europe PMC, and so the handwriting font (Patrick Hand, from Google Fonts) loads when the PDF is made |
| **`pdftoppm`** (optional, from poppler) | turns PDF pages into images so you or an agent can look at them |
| **`pdftotext`** (poppler; only for a paper that is not on Europe PMC) | `scripts/pdf_to_pages.py` uses it to turn a PDF into per-page text |
| **An AI agent that can read and write files and run shell commands** | see section 3. It needs to be capable: the storyboard step is the hardest |

## 2. Set up

```bash
git clone https://github.com/botheredbybees/science-comic-pipeline.git
cd science-comic-pipeline
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest tests -q        # about 110 tests; all should pass
```

**Smoke test with no AI at all.** This runs the checking and drawing half of the pipeline on a finished example:

```bash
.venv/bin/python scripts/validate_storyboard.py examples/pauli-2021-krill-salps-diet/storyboard.yaml
.venv/bin/python scripts/visual_qa.py examples/pauli-2021-krill-salps-diet/storyboard.yaml --keep output/smoke
.venv/bin/python scripts/export_pdf.py examples/pauli-2021-krill-salps-diet/storyboard.yaml -o output/smoke.pdf
```

The validator prints two warnings (jokes still waiting for a human; that is intended), the scan prints
`no defects found`, and `output/smoke.pdf` has 9 A4 pages. If any step fails, see section 6.

### Choosing a paper from a folder of PDFs

If you have a folder of papers and want to know which could be a public comic, run
`.venv/bin/python scripts/triage_papers.py /path/to/papers -o private/triage/<name>` (needs `pdftotext`). It reads each
PDF's DOI, asks Crossref and Unpaywall about the licence (only the DOI leaves your machine), and writes `papers.csv`
(each paper marked `usable`, `check`, `private-only` or `no-doi`) and `topics.csv` (which equipment, collection methods and
analyses the papers mention most). Treat the licence as a lead: confirm it from the article's own text before a public
comic (`skills/source-to-claims`). A `private-only` paper can still be a private reading aid.

## 3. Point your AI environment at the repo

The pipeline is a set of plain Markdown instructions, the five files in `skills/`, plus the scripts they call. Nothing is
tied to one vendor. Open the repo folder in your agent so it can see `AGENTS.md`, which is a short briefing for any
agent. The table says how each common environment picks it up. These tools change quickly, so check your tool's own
documentation if a file name here no longer works; the prompt in section 4 works everywhere.

| Environment | How to set it up | Notes |
|---|---|---|
| **Claude Code** | Run `claude` in the repo folder. It reads `CLAUDE.md`, which imports `AGENTS.md`. To use the five steps as skills it can invoke by name, also run `mkdir -p .claude/skills && cp -r skills/*/ .claude/skills/` | Allow it to run the `.venv/bin/python` scripts, `curl` and `google-chrome`. Works well with one agent doing all five steps; do not hand the whole run to a sub-agent and trust its report |
| **OpenAI Codex CLI** | Run `codex` in the repo folder. It reads `AGENTS.md` natively | Its sandbox may block network and Chrome; allow both (or fetch the paper yourself, see section 6) |
| **Gemini CLI** | Run `gemini` in the repo folder. It reads `GEMINI.md`, which imports `AGENTS.md`. If it ignores the import, set `context.fileName` to `["GEMINI.md", "AGENTS.md"]` in `.gemini/settings.json` | |
| **Cursor** | Open the folder and use Agent mode. It reads `AGENTS.md` | Let it run terminal commands in the integrated terminal |
| **GitHub Copilot** (agent mode in VS Code, or Copilot CLI) | It reads `AGENTS.md`. Or copy its contents into `.github/copilot-instructions.md` | |
| **Another agent or a local model** | Any harness that can edit files and run commands will do. Start with the prompt in section 4 | Use the most capable model you have for step 3 (the storyboard). Small models tend to invent numbers; the validator will catch some but not all |
| **A chat window with no tools** (a web chat, no code execution) | Do the judgement steps in chat and the rest yourself: paste a skill file (for example `skills/source-to-claims/SKILL.md`) with the paper's text, save the YAML the model writes into `examples/<slug>/`, and run the scripts in section 4 yourself, pasting their output back | Slower, but it works. The scripts are the safety net, so never skip them |

## 4. Run it, end to end

Pick a short **slug** for the paper, such as `xia-2024-phytoplankton-pearl-river` (first author, year, topic). If you do
not know the title yet, fetch into `sources/_new` first: `fetch_source.py` prints a suggested slug, and you can rename the
folder. Everything lives under that name: `sources/<slug>/` (the paper's text, never committed) and `examples/<slug>/` (your work).

### The one-prompt way

Paste this into your agent, filling in the DOI and slug:

```text
Turn this open-access paper into a comic using this repo's pipeline.
DOI: <doi>        Slug: <slug>

Read README.md, AGENTS.md and skills/README.md, then follow the five skills in skills/ in order:
source-to-claims, story-spine, storyboard, humour-pass, visual-qa. Use .venv/bin/python for every script.
Stop and tell me if the licence gate refuses the paper.
Every fact in a panel must trace to a verified claim with a quote. Watch for the paper contradicting itself
(Results against Discussion, text against a table) and log every conflict in CLAIM-CHECK.md.
Leave jokes unconfirmed (keeps_claims_intact: false) for me to decide. Do not commit anything.
When you finish, report: the PDF path; the exact commands you ran with their exit codes and key output lines
(check_quotes, validate_storyboard, visual_qa); the jokes awaiting my decision; and every doubt about accuracy.
```

### The step-by-step way

Use this when you want to read what each step produced before the next begins. Each step is one skill; tell the agent
"follow `skills/<name>/SKILL.md`". After each step, run the check yourself.

| Step | Skill | It writes | Run this to check |
|---|---|---|---|
| 1 | `source-to-claims` | `sources/<slug>/` (the paper), `examples/<slug>/claims.yaml`, `CLAIM-CHECK.md` | `.venv/bin/python scripts/check_quotes.py examples/<slug>/claims.yaml --pages-dir sources/<slug>/pages --strict` |
| 2 | `story-spine` | `head.yaml`, `PLAN.md` | read `PLAN.md`: is there a story? |
| 3 | `storyboard` | `beats/B*.yaml`, `storyboard.yaml` | `.venv/bin/python scripts/build_storyboard.py examples/<slug>` then `.venv/bin/python scripts/validate_storyboard.py examples/<slug>/storyboard.yaml --strict` |
| 4 | `humour-pass` | `humour:` blocks on a few panels | the validator should now show one warning per joke and nothing else |
| 5 | `visual-qa` | `QA.md`, `ATTRIBUTION.md`, **`examples/<slug>/<slug>.pdf`** | `.venv/bin/python scripts/visual_qa.py examples/<slug>/storyboard.yaml --keep output/<slug>` reports `no defects found` |

Step 1 starts with `.venv/bin/python scripts/fetch_source.py --doi <doi> -o sources/<slug>`, which prints the paper's
licence and refuses anything that does not allow adaptation. Step 5 ends with
`.venv/bin/python scripts/export_pdf.py examples/<slug>/storyboard.yaml -o examples/<slug>/<slug>.pdf`.

The validator exits with code 1 while a joke awaits you, which is the correct end state.

## 5. Before you share it

A person reads the comic. The scripts check that the numbers match the quotes; they cannot check that the story is fair.

1. **Open the PDF and read every page.** Is any caption stronger than the paper? Does a drawing imply something the paper
   does not say (a worried animal, a chart that looks like data but is a sketch)?
2. **Decide each joke.** They are listed in the agent's report and are the panels with a `humour:` block. Keep, change or
   delete; once you are happy, set `keeps_claims_intact: true` on the ones you keep.
3. **Read `CLAIM-CHECK.md`.** It lists the places the paper contradicted itself and how the comic avoided them.
4. **Check the licence.** `ATTRIBUTION.md` and the last page of the PDF credit the paper, link to it, and name the
   licence. A comic from a CC BY-SA paper must itself be CC BY-SA.
5. **Tell the authors** (courtesy, not a requirement). The footer already says they did not write or endorse it.

## 6. When something goes wrong

| Symptom | Cause and fix |
|---|---|
| `python: command not found`, or `No module named jsonschema` | Use `.venv/bin/python`, not `python`, and run the `pip install` in section 2 |
| `no Chrome or Chromium found` | Install one (`sudo apt install chromium`, or Chrome from google.com/chrome). If the binary has an unusual name, put it on your `PATH` as `google-chrome` |
| PDF text is in a plain fallback font | Patrick Hand loads from Google Fonts at export time; you were offline. Reconnect and export again |
| `fetch_source.py` exits 2 | The paper's licence does not allow adaptation. Stop: choose another paper. (Do not use `--force` for anything you will share) |
| No full text on Europe PMC | Get the PDF from the publisher or a repository, run `.venv/bin/python scripts/pdf_to_pages.py paper.pdf -o sources/<slug>` (try `--mode columns` if two columns are interleaved), and use `check_quotes.py --pages-dir sources/<slug>/pages`. Confirm the licence from the article's own text, write where you found it in `licence_checked`, and say in `meta.source.page_basis` that a claim's `page` is the PDF page index |
| The paper is not open access (the gate refuses it) | Stop, unless you want a **private reading aid** that will never be shared or published: work in `private/<slug>/`, set `meta.private: true` in `head.yaml`, write the real licence ("All rights reserved (...)"), and see `skills/source-to-claims/SKILL.md`. The PDF is stamped "PRIVATE: not for sharing" on every page |
| The agent cannot reach the network | Download the XML in a browser from `https://www.ebi.ac.uk/europepmc/webservices/rest/<PMCID>/fullTextXML` and run `fetch_source.py --xml saved.xml -o sources/<slug>` |
| `check_quotes.py` says a quote is not on its page | The claim's quote was not copied from the page file. Copy it from `sources/<slug>/pages/pNNN.txt`; do not retype it |
| `validate_storyboard.py`: a number appears on the panel but in none of its cited claims | A chart or caption shows a number that no claim contains. Cite the right claim, or take the number out |
| `visual_qa.py` reports overflow or overlap | Shorten the caption, move a character or prop in `staging`, or give a crowded chart a `full` panel. `skills/visual-qa/SKILL.md` has a table |
| The agent says it finished but you doubt it | Re-run the four commands in section 4 yourself and read their output. An agent's report is a claim, not evidence |

## 7. Keeping track of what you have made

Once there is more than a couple of comics, `scripts/catalogue.py` keeps a local index of them. It rebuilds `private/catalogue.db`
(SQLite, not committed) from the comics' files and the triage tables, so it can never disagree with them:

```bash
.venv/bin/python scripts/catalogue.py                  # a summary: each comic, its checks, whether its PDF is stale
.venv/bin/python scripts/catalogue.py --stale          # PDFs older than their storyboard or the renderer
.venv/bin/python scripts/catalogue.py --uses ctd       # which comics use an asset, before you change or retire it
.venv/bin/python scripts/catalogue.py --pending-jokes  # jokes waiting for a person
.venv/bin/python scripts/catalogue.py --todo-papers    # open-licence papers from the triage that are not comics yet
.venv/bin/python scripts/catalogue.py --editions       # when each comic was last made, and against which renderer
```

The one table it does not rebuild is `editions`: every time a comic's PDF has changed, a row records the date, the
renderer's version and the validator's counts, so you can see what changed since a comic was last made. Run
`--stale` after changing the renderer and before sharing a PDF; re-export what it lists.

## 8. What next

- Add a drawing style: a renderer reads `storyboard.yaml` and never the paper. `renderers/xkcd/` is the model.
- Improve a skill: they are plain Markdown. Each of the three cold runs found faults in them; the notes are in
  `skills/README.md` and in the Pauli example's `SKILL-FEEDBACK.md`.
- Send what you made: open an issue or a pull request with the new `examples/<slug>/` folder (the claims ledger, the
  storyboard, `ATTRIBUTION.md` and the PDF; never the paper's text).
