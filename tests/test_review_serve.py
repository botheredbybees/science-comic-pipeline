"""`review_comic.py serve`: the page on this machine, answers saved to a folder, `apply` reading them back. Needs no Claude and no network."""
import json
import shutil
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import review_comic as RC  # noqa: E402
from export_pdf import find_browser  # noqa: E402

EXAMPLE = ROOT / "examples" / "southern-ocean-edna-agreement"


@pytest.fixture
def running(tmp_path):
    comic = tmp_path / "southern-ocean-edna-agreement"
    shutil.copytree(EXAMPLE, comic, ignore=shutil.ignore_patterns("output", "*.pdf"))
    answers = tmp_path / "answers"
    state = {"extra": ""}
    httpd = RC.serve(lambda: RC.build(comic, "southern-ocean-edna-agreement", {}, with_comic=False) + state["extra"], answers, 0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield {"url": f"http://127.0.0.1:{httpd.server_address[1]}", "answers": answers, "comic": comic, "state": state, "port": httpd.server_address[1]}
    httpd.shutdown()
    httpd.server_close()


def call(url, method="GET", body=None, headers=None):
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def put(running, id_, obj, **kw):
    return call(f'{running["url"]}/answers/{id_}', "PUT", json.dumps(obj).encode(), {"Content-Type": "application/json", **kw})


def test_the_page_is_served_and_asks_the_server_for_its_saved_answers(running):
    code, body = call(running["url"] + "/")
    assert code == 200 and b"item-joke-B4_2" in body and b"fetch(\"/answers\"" in body


def test_an_answer_put_to_the_server_lands_in_the_folder_and_comes_back(running):
    ans = {"verdict": "keep", "notes": "fine", "checks": {"0": True}, "edit": {}}
    assert put(running, "joke-B4_2", ans)[0] == 204
    assert json.loads((running["answers"] / "joke-B4_2.json").read_text()) == ans
    assert json.loads(call(running["url"] + "/answers")[1]) == {"joke-B4_2": ans}
    assert not list(running["answers"].glob(".*.tmp"))


def test_the_answers_folder_is_what_apply_reads(running):
    put(running, "joke-B4_2", {"verdict": "keep", "notes": "", "checks": {}, "edit": {}})
    put(running, "general", {"notes": "a general note"})
    res = RC.apply(running["comic"], RC.load_answers(running["answers"]), dry_run=True)
    assert any("B4.2" in line for line in res["done"]) and res["general"] == "a general note"


@pytest.mark.parametrize("bad", ["..", "a%2Fb", "x.json", "%2E%2E%2Fetc", "a" * 81])
def test_an_id_that_is_not_an_item_id_is_refused_and_nothing_is_written(running, bad):
    assert put(running, bad, {"verdict": "keep"})[0] in (400, 404)
    assert not list(running["answers"].glob("*")) and not list(running["answers"].parent.glob("*.json"))


def test_only_json_objects_are_accepted(running):
    assert call(f'{running["url"]}/answers/general', "PUT", b"[1]", {"Content-Type": "application/json"})[0] == 400
    assert call(f'{running["url"]}/answers/general', "PUT", b"{}", {"Content-Type": "text/plain"})[0] == 415


def test_a_request_addressed_to_another_host_is_refused(running):
    assert call(running["url"] + "/answers", headers={"Host": "evil.example"})[0] == 403
    assert put(running, "general", {"notes": "x"}, Host="evil.example")[0] == 403
    assert not running["answers"].exists() or not list(running["answers"].glob("*.json"))


def test_the_page_is_rebuilt_on_each_request_so_a_reload_shows_what_apply_changed(running):
    running["state"]["extra"] = "<!--first-->"
    assert b"<!--first-->" in call(running["url"] + "/")[1]
    running["state"]["extra"] = "<!--second-->"
    assert b"<!--second-->" in call(running["url"] + "/")[1]


@pytest.mark.skipif(find_browser() is None, reason="needs Chrome or Chromium")
def test_in_a_browser_the_page_loads_a_saved_answer_and_saves_a_new_one(running, tmp_path):
    put(running, "joke-B4_2", {"verdict": "keep", "notes": "from the folder", "checks": {}, "edit": {}})
    running["state"]["extra"] = """<script>setTimeout(function(){
      var c=document.querySelector("#item-joke-B4_2"),n=c.querySelector("textarea.notes"),out={loaded:n.value,done:c.classList.contains("done"),
        banner:document.getElementById("banner").className};
      n.value="typed in the browser";n.dispatchEvent(new Event("input",{bubbles:true}));
      setTimeout(function(){out.saved=c.querySelector(".saved").textContent;
        var pre=document.createElement("pre");pre.id="__result";pre.textContent=JSON.stringify(out);document.body.appendChild(pre)},2500)},1500);</script>"""
    r = subprocess.run([find_browser(), "--headless=new", "--disable-gpu", "--no-sandbox", f"--user-data-dir={tmp_path / 'profile'}", "--virtual-time-budget=15000",
                        "--dump-dom", running["url"] + "/"], capture_output=True, text=True, timeout=120)
    import re
    m = re.search(r'<pre id="__result">(.*?)</pre>', r.stdout, re.S)
    assert m, r.stdout[-500:] + r.stderr[-500:]
    out = json.loads(m.group(1).replace("&quot;", '"'))
    assert out["loaded"] == "from the folder" and out["done"] and "hide" in out["banner"]
    assert out["saved"] == "Saved"
    assert json.loads((running["answers"] / "joke-B4_2.json").read_text())["notes"] == "typed in the browser"
