import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from export_pdf import export, find_browser  # noqa: E402

EXAMPLE = ROOT / "examples" / "akam-2026-cartooning" / "storyboard.yaml"
pytestmark = pytest.mark.skipif(find_browser() is None or not Path("/usr/bin/pdfinfo").exists(),
                                reason="needs Chrome or Chromium and pdfinfo")


def test_the_pdf_has_one_a4_page_per_comic_page(tmp_path):
    pdf = export(EXAMPLE, tmp_path / "akam.pdf")
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    assert pages == 2
    assert "A4" in info
    for n in (1, 2):
        text = subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), str(pdf), "-"], capture_output=True, text=True).stdout
        assert f"page {n} of 2" in text
