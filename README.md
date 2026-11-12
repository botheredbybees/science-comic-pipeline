# science-comic-pipeline

Turn a scientific paper into a short comic that stays true to the paper.

Papers and data products reach few people if they only exist as papers. This repo is a
repeatable process for the middle step: **read the paper, pull out what it actually
claims, find the story in it, and hand a structured storyboard to a renderer.**

> **Status: early skeleton.** The storyboard schema and its validator work and are
> tested. The renderers, skills and a full worked example do not exist yet. See
> [the design](docs/superpowers/specs/2026-11-13-science-comic-pipeline-design.md).

## The idea

```
paper ──> claims ledger ──> story spine ──> storyboard.yaml ──> renderer ──> pages
          (cites the        (And / But /     (validated)        (xkcd-style,
           paper)            Therefore)                          painted, ...)
```

- **Every fact in a panel cites a claim, and every claim cites the paper.** The
  validator refuses a panel with a number in it and no claim behind it, and warns
  when a claim has only been checked against the abstract.
- **The storyboard is the product.** Renderers read it and never the paper, so a new
  drawing style is a new renderer and nothing else.
- **Humour is optional and flagged.** A joke on a panel that cites a claim needs a
  reviewer to confirm it leaves the claim intact.

## Try it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/validate_storyboard.py examples/akam-2026-cartooning/storyboard.yaml
.venv/bin/python -m pytest tests -q
```

The example is a draft storyboard of an open-access paper about students learning
biology by drawing cartoons. Its claims come from the abstract only, so the validator
prints one warning per claim until someone checks them against the full text.

## Layout

| Path | What it is |
|---|---|
| `schema/storyboard.schema.json` | The storyboard format (JSON Schema) |
| `scripts/validate_storyboard.py` | Schema check plus the accuracy-ledger rules |
| `examples/` | Example papers, each with its licence record and a storyboard |
| `renderers/` | One folder per drawing style (none yet; interface in its README) |
| `skills/` | Agent skills for the judgement steps (planned; list in its README) |
| `docs/superpowers/` | Design and plans |

## Licences

- **Code and schema:** [MIT](LICENSE).
- **Examples, docs and anything rendered from them:** [CC BY 4.0](LICENSE-CONTENT-CC-BY-4.0.txt).
- **Source papers are not copied here.** Only papers with a licence that allows
  adaptation (CC BY or CC0) are used as examples, and each records where and when
  the licence was checked. See [ATTRIBUTION.md](ATTRIBUTION.md).

If you adapt a paper under a licence with a NoDerivatives clause, you cannot share the
result. Check the licence before you start.
