"""The review page's live preview, run in a headless browser: retyped words appear in every copy of the panel."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import review_comic as RC  # noqa: E402
from export_pdf import find_browser  # noqa: E402

pytestmark = pytest.mark.skipif(find_browser() is None, reason="needs Chrome or Chromium")

PROBE = r"""<script>
(function(){
  var out={};
  function type(el,v){el.value=v;el.dispatchEvent(new Event("input",{bubbles:true}))}
  try{
    var card=document.querySelector("#item-joke-B4_2");
    var pick=function(){return [].slice.call(document.querySelectorAll('[id="panel-B4.2"]'))};
    out.copies=pick().length;
    var lab=card.querySelector('[data-path="split_labels/2"]');
    out.labelOrig=lab.dataset.orig;
    type(lab,"some time later");
    out.afterLabel=pick().map(function(g){return [].map.call(g.querySelectorAll("text"),function(t){return t.textContent}).filter(function(x){return /soon|later/.test(x)})});
    var cap=card.querySelector('[data-line="0"] textarea'),capOrig=cap.value;
    var g0=pick()[0],capEl=[].filter.call(g0.querySelectorAll("text"),function(t){return t.getAttribute("data-wrap")&&/MZG-ICE/.test(t.textContent)})[0];
    var linesBefore=capEl.querySelectorAll("tspan").length,boxBefore=capEl.previousElementSibling.getAttribute("height");
    type(cap,capOrig+" This sentence was added by the reviewer to test that the grey box grows and the words wrap.");
    out.capLines=[linesBefore,capEl.querySelectorAll("tspan").length];
    out.capBox=[boxBefore,capEl.previousElementSibling.getAttribute("height")];
    var per=Math.floor(parseFloat(capEl.getAttribute("data-wrap"))/(parseFloat(capEl.getAttribute("font-size"))*0.46));
    out.capWrapOk=[].every.call(capEl.querySelectorAll("tspan"),function(s){return s.textContent.length<=per});
    var ines=card.querySelector('[data-line="1"] textarea');
    type(ines,"Ten labs. Ten protocols. Ten headaches, honestly.");
    var sayEl=[].filter.call(g0.querySelectorAll("text"),function(t){return /headaches/.test(t.textContent)})[0];
    var hal=0,p=sayEl.previousElementSibling;while(p&&p.tagName==="rect"&&p.getAttribute("rx")==="3"){hal++;p=p.previousElementSibling}
    out.sayLines=sayEl.querySelectorAll("tspan").length;out.sayHalos=hal;
    type(cap,capOrig);type(ines,ines.dataset.orig);
    out.capBack=[capEl.querySelectorAll("tspan").length===linesBefore,capEl.previousElementSibling.getAttribute("height")===boxBefore];
    out.sayBack=/Ten labs, ten protocols\./.test(pick()[0].textContent);
    var rm=card.querySelector('[data-line="2"] [data-e=remove]');rm.checked=true;rm.dispatchEvent(new Event("change",{bubbles:true}));
    var otto=[].filter.call(pick()[1].querySelectorAll("text"),function(t){return /Ridiculous/.test(t.textContent)})[0];
    out.removedHidden=otto.style.display==="none";
    out.edited=card.classList.contains("edited");
  }catch(e){out.error=String(e&&e.stack||e)}
  var pre=document.createElement("pre");pre.id="__result";pre.textContent=JSON.stringify(out);document.body.appendChild(pre);
})();
</script>
"""


def test_retyped_words_show_in_the_card_and_in_the_full_comic_and_revert_exactly(tmp_path):
    dest = tmp_path / "southern-ocean-edna-agreement"
    shutil.copytree(ROOT / "examples" / "southern-ocean-edna-agreement", dest, ignore=shutil.ignore_patterns("output", "*.pdf"))
    page = tmp_path / "page.html"
    page.write_text(RC.build(dest, "southern-ocean-edna-agreement", {}, "unverified") + PROBE)
    run = subprocess.run([find_browser(), "--headless=new", "--no-sandbox", "--virtual-time-budget=4000", "--dump-dom", f"file://{page}"],
                         capture_output=True, text=True, timeout=120)
    got = json.loads(re.search(r'<pre id="__result">(.*?)</pre>', run.stdout, re.S).group(1).replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">"))
    assert "error" not in got, got.get("error")
    assert got["copies"] == 2  # the card's picture and the page of the full comic
    assert got["labelOrig"] == "soon" and got["afterLabel"] == [["some time later"], ["some time later"]]
    assert got["capLines"][1] > got["capLines"][0] and float(got["capBox"][1]) > float(got["capBox"][0]) and got["capWrapOk"]
    assert got["sayLines"] == got["sayHalos"] >= 2  # each wrapped line of a speech block keeps its white patch
    assert got["capBack"] == [True, True] and got["sayBack"]  # clearing the edit restores the original drawing
    assert got["removedHidden"] and got["edited"]
