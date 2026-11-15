# Setting up your own pipeline

This page is for someone starting from an empty machine who wants to run the pipeline with whatever hardware, models and
subscriptions they have. [HOWTO.md](../HOWTO.md) is the guide to making a comic; this is the guide to getting ready to.

**Nothing here depends on a particular vendor, cloud account, subscription or computer.** The checking, drawing and PDF export
are ordinary Python scripts. A language model is used in two separate places, and you can swap or skip either:

| Where a model is used | What it does | Required? | What can fill the role |
|---|---|---|---|
| **The agent** that follows the five skills | Reads a paper, writes the claims, finds the story, writes the storyboard | Yes, unless you do these steps yourself | Any coding agent (Claude Code, Codex, Gemini CLI, Cursor, Copilot, an open-source agent) or a chat window, or you by hand: [HOWTO section 3](../HOWTO.md) |
| **The card tools** (`extract_cards.py`, `verify_cards.py`) | Drafts claims with quotes from a PDF, and gives a second opinion on them | No: they save typing; you can write claims by hand | A model running on your own machine, a model on a server you run, or a hosted service: this page, section 4 |

The pictures are never made by a model. They are drawn by the renderer from the storyboard.

## 1. The core install (no model, no GPU)

You need:

| | Why | Check |
|---|---|---|
| Python 3.10 or newer, and `git` | the scripts and tests | `python3 --version` |
| Chrome or Chromium | exports the PDF (headless) | `chromium --version` or `google-chrome --version` |
| `pdftotext` and `pdfinfo` (poppler-utils) | turns a PDF into numbered pages of text | `pdftotext -v` |
| `curl` | fetches open-access papers from Europe PMC | `curl --version` |
| An internet connection at export time | the handwriting font loads from Google Fonts; offline, the PDF falls back to a plain font | |

On Debian or Ubuntu: `sudo apt install python3-venv git chromium poppler-utils curl`. The project is developed and tested on Linux. It
uses only portable Python and standard tools, so macOS (Homebrew: `brew install poppler`, plus Chrome from google.com/chrome) should work, and Windows is best run
inside WSL, but neither has been tested here.

```bash
git clone https://github.com/botheredbybees/science-comic-pipeline.git
cd science-comic-pipeline
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest tests -q
```

All tests should pass. Then prove the drawing half works, with no model at all:

```bash
.venv/bin/python scripts/validate_storyboard.py examples/pauli-2021-krill-salps-diet/storyboard.yaml
.venv/bin/python scripts/visual_qa.py examples/pauli-2021-krill-salps-diet/storyboard.yaml --keep output/smoke
.venv/bin/python scripts/export_pdf.py examples/pauli-2021-krill-salps-diet/storyboard.yaml -o output/smoke.pdf
```

Expect two warnings (jokes waiting for a human), `no defects found`, and a 9-page PDF. If you get this far, the machine is ready for
everything except the model steps.

## 2. Choose your agent

Any tool that can read and write files and run shell commands, and that is capable enough for the storyboard step. Setting up
each common tool is a table in [HOWTO section 3](../HOWTO.md). What matters for cost and quality:

- The agent steps are the expensive ones. A full run on a 10-page open-access article has taken an agent about 15 minutes and
  300,000 tokens.
- Use the most capable model you have for the storyboard (step 3). Small models tend to invent numbers; the validator catches
  that, but each catch costs a round trip.
- A model that cannot run commands can still do the judgement steps in a chat window while you run the scripts yourself.

## 3. Keep your settings in one place

Model settings live in environment variables, so nothing about your machine is written into the repo. Copy the example and edit it:

```bash
cp .env.example .env          # .env is git-ignored
set -a; source .env; set +a   # `source` alone does not export the variables to the scripts
.venv/bin/python scripts/llm.py --ping
```

`--ping` sends one tiny request and prints the reply and the time it took. If it fails, the message says why (cannot reach the
server, wrong key, no such model). Do this before any long run.

## 4. The card tools: pick a model

The card tools talk to a model through one small client, `scripts/llm.py`. It speaks three kinds of API, and you choose with three
settings.

| Setting | Means |
|---|---|
| `LLM_BACKEND` | `ollama`, `openai` or `anthropic` |
| `LLM_BASE_URL` | where the server is |
| `LLM_MODEL` | the model's name on that server |
| `LLM_API_KEY` | only for a hosted service. Keep it in `.env`, never on a command line |
| `LLM_VERIFY_MODEL` | the model that checks the cards (see below) |

| If you use | Set |
|---|---|
| **Ollama** on this machine or another | `LLM_BACKEND=ollama`, `LLM_BASE_URL=http://localhost:11434` (or the other machine's address), `LLM_MODEL=<a name from `ollama list`>` |
| **llama.cpp** (`llama-server`), **vLLM**, **LM Studio**, **LocalAI** or any server with an OpenAI-compatible API | `LLM_BACKEND=openai`, `LLM_BASE_URL=http://localhost:8080/v1` (the address up to `/v1`), `LLM_MODEL=<its model name>` |
| **Ollama's OpenAI-compatible address** | `LLM_BACKEND=openai`, `LLM_BASE_URL=http://localhost:11434/v1` |
| A **hosted** OpenAI-compatible service (OpenRouter, OpenAI and others) | `LLM_BACKEND=openai`, `LLM_BASE_URL=<its /v1 address>`, `LLM_API_KEY`, `LLM_MODEL` |
| **Anthropic's API** | `LLM_BACKEND=anthropic`, `LLM_MODEL=<model>`, `LLM_API_KEY` |

`python scripts/llm.py --list` shows the model names a server offers (Ollama and OpenAI-compatible servers).

### How big a model, and what hardware

You do not need a large machine, and the design means a weak model cannot invent a quotation: every quote a model offers is
forced onto the real words of the page, or the card is dropped (`scripts/snap_quotes.py`). A weak model gives you fewer cards, or
loose paraphrases, not invented evidence. What a model can still get wrong is the paraphrase, which is why the cards start
`unverified` and a person reads them (section 5).

What the project has measured, on **one** machine (a 128 GB unified-memory workstation running Ollama), extracting claims from a
15-page book chapter. "Found on the named page" is the share of the model's quotes that were exact copies of the page it named;
"verified after snapping" is the share that matched the page text once each quote was snapped to its nearest real words:

| Model (size on disk) | Found on the named page | Verified after snapping | Time for the chapter |
|---|---|---|---|
| a 27B dense model (18 GB) | 76% | 99% | about 5 minutes |
| a 120B mixture-of-experts model (90 GB) | 72% | 98% | about 7 minutes |
| a 35B mixture-of-experts model (23 GB) | 67% | 98% | not recorded |
| a 122B model (77 GB) | 67% | 96% | about 4 minutes |

A larger model was not better at extraction: the smallest of these, the 27B model, scored highest. These are single-run measurements
on one document, so treat them as a starting point, not a ranking. Smaller models than these were not tested.

| Your hardware | A reasonable start |
|---|---|
| **No GPU, a laptop, or a small machine** | A hosted service (section above), or a small local model with `--window-words 3000`. Expect fewer cards and more that are dropped. Not tested here |
| **A 16 to 24 GB GPU** | A model of about 7B to 30B parameters. Raise `--window-words` as far as the model's context allows |
| **Large unified memory (64 GB or more)** | The measured models above, or larger ones for the checking model |

Two settings matter more than the hardware:

- **`--window-words`** (default 14,000) is how much page text goes in each request. Pick it for the model's context window: about
  3,000 for an 8,000-token context, about 14,000 for a 32,000-token one. A long document is read in overlapping windows.
- **The checking model.** `verify_cards.py` asks a second model whether each paraphrase says more than its quote. Use a different model
  from the extractor, and a larger one if you can. In one test with 12 planted errors among 48 cards, a 122B model caught all 12 and
  wrongly flagged 2 of 36 clean cards; a 27B model caught all 12 and wrongly flagged 8 of 36. Either way the flags are a reading list for
  a person, not a verdict.

### Privacy

A model you run yourself keeps the paper on your machine. A hosted service receives the **full text** of every page you extract
from. That is fine for an open-access paper. For a copyrighted reading you only hold a private copy of (the `private/` route in the
HOWTO), check the provider's terms first, or use a local model.

## 5. Using the card tools

```bash
set -a; source .env; set +a
.venv/bin/python scripts/intake_check.py paper.pdf                       # is it scanned, a reference list, a fragment? licence hints
.venv/bin/python scripts/extract_cards.py paper.pdf -o cards/<slug> --ref <slug>
.venv/bin/python scripts/verify_cards.py cards/<slug>/cards.yaml        # second opinion; uses LLM_VERIFY_MODEL
.venv/bin/python scripts/cards_to_claims.py --from <slug>=cards/<slug>:all -o examples/<slug>/claims.yaml --show
```

Cards can also build a reading wiki, not only comics: `select_key_cards.py` picks a paper's key cards (the model chooses ids and writes no
text), `cards_to_source_page.py` lays them out as a page where every line carries its page number and its quote, `topic_from_cards.py`
writes a topic page from several papers with every statement checked against the cards it cites (and any number it states against
those cards), and `suggest_graphics.py` proposes pictures a comic could draw for each paper, then ranks the assets the renderer lacks.
The model steps (`select_key_cards`, `topic_from_cards`, `suggest_graphics`) use the same `LLM_*` settings as the card tools.

`extract_cards.py` also takes a **folder** of PDFs and writes one card set for each, skipping any that `intake_check` finds to be
scanned, a reference list or a fragment. The last step turns cards into the claims ledger the storyboard uses, from one paper or several
(see [HOWTO, "One paper, or several?"](../HOWTO.md)). The cards are not claims until a person has read each paraphrase against its quote:
see `skills/source-to-claims/SKILL.md`.

## 6. When something fails

| Symptom | Likely cause |
|---|---|
| `llm.py --ping`: `could not reach ...` | wrong address or port, the server is not running, or a firewall; on another machine, the server may listen only on localhost |
| `answered 401` | missing or wrong `LLM_API_KEY`; remember `set -a; source .env; set +a` |
| `answered 404` and the model's name | the model is not installed on that server: `llm.py --list` |
| Every card is dropped | the model's quotes are not copies of the page text; try a larger model, or a smaller `--window-words`; check `pages/*.txt` is readable text and not garbled (a scanned PDF needs OCR first) |
| Very few cards from a long paper | the reply was cut off: raise `--max-tokens`, or lower `--window-words` |
| The reply is not JSON | a model that cannot follow a format: try another. The extractor salvages a truncated list but not prose |
| `extract_cards.py` is very slow | a model too large for the machine is swapping; use a smaller one. |

## 7. A checklist for a new machine

1. `python3 --version` is 3.10 or newer; `chromium` or `google-chrome`, `pdftotext` and `curl` run.
2. `.venv/bin/python -m pytest tests -q` passes.
3. The smoke test in section 1 gives a 9-page PDF.
4. Your agent reads `AGENTS.md` (HOWTO section 3).
5. Only if you will use the card tools: `.env` is filled in and `scripts/llm.py --ping` answers.

Then follow [HOWTO.md](../HOWTO.md) from section 4.
