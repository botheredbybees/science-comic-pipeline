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

## Rules that are not negotiable

- **Every fact in a panel traces to a claim, and every claim to a quote on a page of the paper.** Do not write a fact from
  memory. Do not make a caption stronger than its claim (keep hedges, numbers, units and scope).
- **Only CC BY, CC BY-SA and CC0 papers.** If `fetch_source.py` refuses a licence, stop and tell the user.
- **Run the checks yourself and report what they print**, never what you expect: `check_quotes.py --strict`,
  `validate_storyboard.py --strict`, `visual_qa.py`. Do not trust a summary from another agent.
- **Jokes are the user's call.** Leave `keeps_claims_intact: false` unless a joke passes the five questions in the humour skill; the user
  reads and approves them with `scripts/jokes.py` (`list`, `show`, `approve`, `review`). **Vary the frames**: label every transition and
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
