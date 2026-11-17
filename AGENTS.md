# Instructions for AI agents working in this repository

This repo turns an open-access scientific paper into an accurate comic. **Read [HOWTO.md](HOWTO.md) for the whole
process and [skills/README.md](skills/README.md) for the five steps**; this file is the short version.

## The job

Given a DOI, follow the five skills in `skills/`, in order, and finish with a PDF:

1. `skills/source-to-claims/SKILL.md`: fetch the paper, check its licence, write `claims.yaml` (verbatim quotes).
2. `skills/story-spine/SKILL.md`: `head.yaml` and `PLAN.md`.
3. `skills/storyboard/SKILL.md`: `beats/B*.yaml`, then build and validate.
4. `skills/humour-pass/SKILL.md`: a few flagged jokes at most.
5. `skills/visual-qa/SKILL.md`: scan, look at every page, export the PDF, write `ATTRIBUTION.md`.

Work in `examples/<slug>/` (or `private/<slug>/` if the licence is not confirmed). Sources go in `sources/<slug>/`.

**Before step 2 and again before step 3, read `private/lore/COMIC-LORE.md` if it exists** (its "How to use" section, Part A: what this project has
found out, and Part B: McCloud's transitions and the split screen; Parts C to G when a question needs them). It is local only (gitignored, because
it paraphrases books), so a fresh clone will not have it: carry on without it and do not recreate it. It is advice about shape, and the rules in this
file win over it: it never licenses a fact, a motive, or a dramatic beat the paper does not give.

## Two choices to make before step 1

- **One paper or several?** A comic retells one paper (`meta.source`) or what several papers say about one question, a topic comic
  (`meta.sources`, and a `source.ref` on every claim). `HOWTO.md` ("One paper, or several?") says when to choose each and the rules.
- **A model for drafting claims?** Optional. `scripts/extract_cards.py` drafts claims with quotes from a PDF using any model the user has
  set up; its quotes are real page text, but its paraphrases are drafts until you have read each against its quote. Setup, model
  choice and hardware are in `docs/SETUP.md`; nothing in the pipeline requires a particular vendor or machine.

## Rules that are not negotiable

- **Every fact in a panel traces to a claim, and every claim to a quote on a page of the paper.** Do not write a fact from
  memory. Do not make a caption stronger than its claim (keep hedges, numbers, units and scope).
- **Only CC BY, CC BY-SA and CC0 papers.** If `fetch_source.py` refuses a licence, stop and tell the user.
- **Run the checks yourself and report what they print**, never what you expect: `check_quotes.py --strict`,
  `validate_storyboard.py --strict`, `visual_qa.py`. Do not trust a summary from another agent.
- **Jokes are the user's call.** Leave `keeps_claims_intact: false` unless a joke passes the six questions in the humour skill; the user
  reads and approves them with `scripts/jokes.py` (`list`, `show`, `approve`, `review`) or on the web page `scripts/review_comic.py build` makes (it also lists claims to verify and panels; `apply` reads the answers back). **Publishing and reading back are yours to do** (HOWTO section 7): publish the built page as a private Artifact with `capabilities: {db: {}}` and give the user that claude.ai link, never the local file or a `http.server` copy (no database, so Submit cannot save); when the user says "submitted", list the collection `review` with `ArtifactData` (`out_dir` set), run `apply --dry-run`, then `apply`, work the worklist, re-run the checks, re-export the PDF, rebuild and republish. Never publish a private comic's page for anyone but the user. **Vary the frames**: label every transition and
  word-picture honestly, use the `gloss` and `moment` devices, and check with `validate_storyboard.py --variety` (see `skills/storyboard`).
- Black and white only. No image models: the pictures come from the storyboard's `staging` and the renderer.
- Do not commit or push unless asked. When a job says "never run git", that includes read-only commands such as `git status`.
- A paper that is not open access is never worked on in `examples/`. Only if the user asks for a private reading aid:
  work in `private/<slug>/` with `meta.private: true`, and never publish or share the result (see `skills/source-to-claims`).

## Commands

Use the repo's interpreter, `.venv/bin/python` (setup is in the HOWTO). `python -m pytest tests -q` runs the tests; run
them after any change to `scripts/` or `renderers/`. The staging vocabulary (characters, appearance, props, charts) is in
`renderers/README.md`. `scripts/catalogue.py --stale` lists comics whose PDF is out of date, and `--uses <asset>` shows which comics use an
asset before you change or retire it.
