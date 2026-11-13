Read AGENTS.md in this folder first; it is the instruction file for every AI tool that works here.

@AGENTS.md

# Notes for Claude Code sessions

The rules above apply. This section adds what a Claude Code session needs that other tools do not.

## Where things stand

- The repo is **public** (https://github.com/botheredbybees/science-comic-pipeline). Anything committed is world-readable:
  no private paths, emails, tokens or unreleased material in files or commit messages.
- Code is MIT; docs and content are CC BY 4.0; a comic inherits its source paper's licence (ShareAlike included).
- Tracked examples are exactly two: `examples/akam-2026-cartooning/` and `examples/pauli-2021-krill-salps-diet/`, each with
  its PDF. Every other comic lives in `private/` (gitignored, local only). **Do not add a third example, and do not move a
  comic out of `private/`, unless the user asks.**
- `.gitignore` ignores `*.pdf` except `examples/*/*.pdf`, and ignores `private/`, `sources/` and `output/`. Never commit a
  paper's text (`sources/`).
- Ten papers were run cold through the skills (Strzepek, Pauli, Lin 2021, Xia, then six private eDNA comics). Each run found
  skill, script or doc faults and they were fixed; `skills/README.md` records the runs.
- Two jokes in the Pauli example (B4.5, B6.1) are still `keeps_claims_intact: false`, so its validator prints two warnings.
  That is the intended "awaiting a human" state. Only the user confirms a joke.

## Setup and checks

```bash
.venv/bin/python -m pytest tests -q        # 133 tests; run after any change to scripts/ or renderers/
.venv/bin/python scripts/validate_storyboard.py examples/<slug>/storyboard.yaml --strict
.venv/bin/python scripts/visual_qa.py examples/<slug>/storyboard.yaml --keep output/<slug>
.venv/bin/python scripts/export_pdf.py examples/<slug>/storyboard.yaml -o examples/<slug>/<slug>.pdf
```

If `.venv` is missing: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`. PDF export needs
Chrome or Chromium and an internet connection (the Patrick Hand font loads from Google Fonts).

The PDF (A4, font embedded, clickable footer links) is the deliverable. Send it to the user with `SendUserFile`; Claude
artifacts are previews only. The PDF is produced by scripts alone, with no model and no image generation.

## Working here

- **Run the check and read its output; do not report what you expect.** An agent's report of success is a claim: re-run
  `check_quotes.py --strict`, `validate_storyboard.py --strict` and `visual_qa.py` yourself, then look at the PDF pages.
- **Cold-testing the skills** is done with a fresh non-fork `general-purpose` agent told not to use the Agent tool, not to
  read other examples, `private/` or `output/`, and not to run git, keeping a `SKILL-FEEDBACK.md`. Fix every fault it
  finds in the skills, scripts or docs, then re-run the checks.
- **Stage files by name when committing** (`git add path ...`), never `git add -A .`. Once that swept an unapproved
  `private/` comic into a public commit. Commit and push only when asked.
- The repo's git author email is the GitHub noreply address; leave it. The commit trailers in this repo are fine (a
  personal GitHub repo, unlike the user's shared Bitbucket repos).
- **Characters may be silly, but breakout boxes and captions must be accurate.** The user approves jokes that keep the
  claims intact; the scripts cannot judge a joke, so never set `keeps_claims_intact: true` yourself.
- Staging vocabulary (hair, coats, bodies, poses, held objects, props, charts) is in `renderers/README.md`; the schema is
  `schema/storyboard.schema.json`. Keep the two in step with `renderers/xkcd/render.py` and `props.py` when adding any option.
- Do not use `rm` with shell variables (the sandbox refuses it); write to new file names instead.

## Known limits (see `renderers/README.md`)

The `up` pose with a mug puts the mug at the ear; thermometer and laptop props are plain; the overflow scan cannot see a
leader line crossing text, so look at every page; figures in a paper are not read by the scripts (only text and tables),
so any number taken from a figure needs a human look at that figure.
