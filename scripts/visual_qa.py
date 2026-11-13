#!/usr/bin/env python3
"""Render a storyboard and scan the pages for defects a script can see.

    python scripts/visual_qa.py examples/lin-2017-wap-npc/storyboard.yaml
    python scripts/visual_qa.py storyboard.yaml --keep out/qa     (also keep the rendered pages)

It loads the rendered pages in headless Chrome or Chromium and reports, per page and panel:
  overflow   text that runs past the edge of its page
  overlap    two pieces of text whose boxes cross
It exits 1 if there is any defect. It cannot see text running over a drawing, a drawing that
overlaps another, or a figure that reads badly: look at the pages as well (see skills/visual-qa).
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "renderers" / "xkcd"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402
from export_pdf import find_browser  # noqa: E402

SCAN = r"""
<pre id="qa-result"></pre>
<script>
window.addEventListener('load', () => document.fonts.ready.then(() => {
  const out = {pages: [], overflow: [], overlap: []};
  const label = t => (t.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40);
  const panelOf = t => { const g = t.closest('g[id^="panel-"]'); return g ? g.id.replace('panel-', '') : ''; };
  document.querySelectorAll('.page > svg').forEach((svg, i) => {
    const sr = svg.getBoundingClientRect();
    const texts = [...svg.querySelectorAll('text')].map(t => ({t, r: t.getBoundingClientRect()}));
    out.pages.push({page: i + 1, texts: texts.length, panels: svg.querySelectorAll('g[id^="panel-"]').length});
    texts.forEach(({t, r}) => {
      if (r.width && (r.left < sr.left - 1 || r.right > sr.right + 1 || r.top < sr.top - 1 || r.bottom > sr.bottom + 1))
        out.overflow.push({page: i + 1, panel: panelOf(t), text: label(t)});
    });
    for (let a = 0; a < texts.length; a++) for (let b = a + 1; b < texts.length; b++) {
      const p = texts[a].r, q = texts[b].r;
      if (!p.width || !q.width) continue;
      const w = Math.min(p.right, q.right) - Math.max(p.left, q.left), h = Math.min(p.bottom, q.bottom) - Math.max(p.top, q.top);
      if (w > 3 && h > 0.3 * Math.min(p.height, q.height)) out.overlap.push({page: i + 1, panel: panelOf(texts[a].t), text: label(texts[a].t), other: label(texts[b].t)});
    }
  });
  document.getElementById('qa-result').textContent = JSON.stringify(out);
}));
</script>
"""


def scan(storyboard, keep=None, browser=None, wait_ms=15000):
    """Render the storyboard and return the scan result as a dict."""
    browser = browser or find_browser()
    if not browser:
        raise RuntimeError("no Chrome or Chromium found")
    doc = yaml.safe_load(Path(storyboard).read_text())
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(keep) if keep else Path(tmp)
        render.render(doc, str(out), standalone=True)
        sheet = out / "sheet.html"
        probe = out / "qa-probe.html"
        probe.write_text(re.sub(r"</body>", lambda m: SCAN + "</body>", sheet.read_text(), count=1)
                         if "</body>" in sheet.read_text() else sheet.read_text() + SCAN)
        done = subprocess.run([browser, "--headless=new", "--no-sandbox", "--disable-gpu", f"--virtual-time-budget={wait_ms}",
                               "--dump-dom", f"file://{probe}"], capture_output=True, text=True, timeout=180)
        m = re.search(r'<pre id="qa-result">(.*?)</pre>', done.stdout, re.S)
        if not m or not m.group(1).strip():
            raise RuntimeError("the scan produced no result (did the page load?)")
        probe.unlink()
        return json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("storyboard")
    ap.add_argument("--keep", help="folder to keep the rendered pages in")
    args = ap.parse_args(argv)
    res = scan(args.storyboard, args.keep)
    pages = res["pages"]
    print(f"{len(pages)} page(s), {sum(p['panels'] for p in pages)} panel(s), {sum(p['texts'] for p in pages)} text item(s)")
    for kind in ("overflow", "overlap"):
        for d in res[kind]:
            extra = f" / {d['other']!r}" if "other" in d else ""
            print(f"{kind}: page {d['page']}, panel {d['panel'] or '?'}: {d['text']!r}{extra}")
    n = len(res["overflow"]) + len(res["overlap"])
    print("no defects found" if not n else f"{n} defect(s)")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
