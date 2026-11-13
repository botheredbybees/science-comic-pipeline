import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from pdf_to_pages import clean, main  # noqa: E402

needs_poppler = pytest.mark.skipif(not shutil.which("pdftotext"), reason="poppler is not installed")


def test_clean_drops_publisher_footer_lines_only():
    text = "Real sentence one.\n1365294x, 2021, 13, Downloaded from https://onlinelibrary.wiley.com/doi/x by Someone\nReal sentence two.\f"
    out, dropped = clean(text)
    assert dropped == 1
    assert "Downloaded" not in out and "Real sentence one." in out and "Real sentence two." in out


@needs_poppler
def test_writes_one_numbered_file_per_pdf_page(tmp_path, capsys):
    pdf = next((ROOT / "examples").glob("*/*.pdf"), None)
    if pdf is None:
        pytest.skip("no example PDF to read")
    assert main([str(pdf), "-o", str(tmp_path)]) == 0
    pages = sorted((tmp_path / "pages").glob("p*.txt"))
    assert pages and pages[0].name == "p001.txt"
    assert "page(s) written" in capsys.readouterr().out
    assert main([str(pdf), "-o", str(tmp_path / "c"), "--mode", "columns"]) == 0
