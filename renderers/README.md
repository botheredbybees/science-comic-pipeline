# Renderers

A renderer turns a validated `storyboard.yaml` into page images or SVG. None exists yet.

## Interface (draft)

A renderer is a folder `renderers/<style>/` with a `render.py` exposing:

```python
def render(storyboard: dict, out_dir: Path) -> list[Path]:
    """Write one file per page into out_dir and return their paths."""
```

Rules every renderer follows:
- Read the storyboard only. Never open the source paper.
- Draw each panel's `scene`, `speech` and `frame`. Do not add facts.
- If a panel has `humour`, render it; a reviewer decides whether it stays.
- Keep text as real text (SVG `<text>`, not outlines) so it can be checked and edited.

## Planned

| Style | Notes |
|---|---|
| `xkcd/` | Stick figures; outlined and borderless panels; wobble on lines and curves; a short connector line from text to speaker; almost no colour. First to build, as the comparison against a hand-painted version. |
| `painted/` | Layered, textured SVG in the manner of a ligne-claire or Franco-Belgian album. Expensive to author by hand; may need an image model. |
