#!/usr/bin/env python3
"""Build a review form as one self-contained web page, for any checklist of things to look at and judge.

A page made here shows, for each item, its pictures, a list of things to check, a keep / fix / drop verdict and a notes box, and saves
each answer as it is given. Published as an Artifact with the `db` capability, the answers are stored in the artifact's database under the
collection `review` (or `collection=`; one document per item id, plus `general`, and `_submitted` when the Submit button is pressed), where Claude can read them back with the ArtifactData tool.
Open the same file in a plain browser and it still works, keeping answers in that browser only.

    from review_form import build_html
    html = build_html("Asset review", "what to do", groups)

`groups` is [(group title, [item, ...])] and an item is {"id": "A1", "name": "stage", "variants": [{"id": "A1a", "label": "plain", "svg": "<svg ...>"}],
"checks": ["what to look for", ...]}. `scripts/review_sheet.py --html` builds one for the new drawing assets.
"""
import html as H
import json

FONT = '"Patrick Hand", "Comic Neue", "Comic Sans MS", cursive'


def framed_svg(inner, label, w=640, h=420):
    """Wrap drawing markup (in a w by h box) as a standalone inline <svg> with its own viewBox and the comic font."""
    return (f'<svg class="fig" viewBox="0 0 {w} {h}" role="img" aria-label="{H.escape(label, quote=True)}" font-family=\'{FONT}\'>{inner}</svg>')


def _opts(values, current="", blank=None):
    """<option> list; `blank` adds an empty first choice with that label. A current value outside `values` is kept."""
    vals = list(values)
    if current and current not in vals:
        vals.insert(0, current)
    out = [f'<option value=""{" selected" if not current else ""}>{H.escape(blank)}</option>'] if blank is not None else []
    out += [f'<option value="{H.escape(v, quote=True)}"{" selected" if v == current else ""}>{H.escape(v)}</option>' for v in vals]
    return "".join(out)


def _sel(field, label, values, current="", blank=None):
    return (f'<label>{H.escape(label)} <select data-e="{field}" data-orig="{H.escape(current, quote=True)}">'
            f'{_opts(values, current, blank)}</select></label>')


def edit_html(e):
    """The optional 'change the picture' block: scene text, each character's action, face, facing and what they hold, each prop, and one added prop or character."""
    v = e["vocab"]
    scene = e.get("scene", "")
    rows = [f'<label class="fld">Scene <textarea data-e="scene" data-orig="{H.escape(scene, quote=True)}" rows="2">{H.escape(scene)}</textarea></label>']
    for i, ln in enumerate(e.get("lines", [])):
        rows.append(f'<div class="erow line" data-line="{i}"><b>{H.escape(ln["who"])}</b>'
                    f'<textarea data-e="text" data-orig="{H.escape(ln["text"], quote=True)}" rows="2" aria-label="Words spoken by {H.escape(ln["who"], quote=True)}">{H.escape(ln["text"])}</textarea>'
                    '<label class="chk"><input type="checkbox" data-e="remove"> Remove</label></div>')
    if "lines" in e:
        rows.append('<div class="erow line" data-addline>' + _sel("speaker", "Add a line", [c["id"] for c in e["cast"]] + ["caption"], "", "(none)")
                    + '<textarea data-e="text" rows="2" placeholder="What it says" aria-label="Words for the added line"></textarea></div>')
    for i, c in enumerate(e["characters"]):
        rows.append(f'<div class="erow" data-char="{i}"><b>{H.escape(c["name"])}</b>'
                    + _sel("pose", "Action", v["poses"], c.get("pose", ""), "(none)") + _sel("face", "Face", v["faces"], c.get("face", ""), "(none)")
                    + _sel("facing", "Facing", v["facings"], c.get("facing", ""), "(default)") + _sel("holding", "Holding", v["holdings"], c.get("holding", ""), "(nothing)") + "</div>")
    for i, p in enumerate(e["props"]):
        label = p.get("label", "")
        rows.append(f'<div class="erow" data-prop="{i}">' + _sel("kind", "Prop", v["kinds"], p["kind"])
                    + f'<label>Label <input type="text" data-e="label" data-orig="{H.escape(label, quote=True)}" value="{H.escape(label, quote=True)}"></label>'
                    + '<label class="chk"><input type="checkbox" data-e="remove"> Remove</label></div>')
    rows.append('<div class="erow" data-addprop>' + _sel("kind", "Add a prop", v["kinds"], "", "(none)") + '<label>Label <input type="text" data-e="label" value=""></label></div>')
    rows.append('<div class="erow" data-addchar>' + _sel("id", "Add a character", [c["id"] for c in e["cast"]], "", "(none)")
                + _sel("pose", "Action", v["poses"], "", "(default)") + _sel("face", "Face", v["faces"], "", "(default)") + _sel("facing", "Facing", v["facings"], "", "(default)") + "</div>")
    return ('<details class="edit"><summary>Change the words, scene, characters, props or actions</summary>'
            '<p class="meta">Pick what should be different. Claude applies it to the storyboard and redraws; added props and characters are placed at a default spot, so look at the new picture.</p>'
            + "".join(rows) + "</details>")


def item_html(it):
    labels = it.get("labels") or {}
    figs = "".join(f'<figure><div class="plate">{v["svg"]}</div><figcaption><b>{H.escape(v["id"])}</b> {H.escape(v["label"])}</figcaption></figure>' for v in it["variants"])
    checks = "".join(f'<li><label><input type="checkbox" data-k="{i}"> <span>{H.escape(c)}</span></label></li>' for i, c in enumerate(it["checks"]))
    return (f'<article class="card" id="item-{H.escape(it["id"])}" data-id="{H.escape(it["id"])}">'
            f'<header><h3><span class="tag">{H.escape(it["id"])}</span> {H.escape(it["name"])}</h3>'
            f'<div class="verdict" role="radiogroup" aria-label="Verdict for {H.escape(it["name"])}">'
            + "".join(f'<label class="v-{v}"><input type="radio" name="v-{H.escape(it["id"])}" value="{v}"><span>{H.escape(labels.get(v, v.title()))}</span></label>' for v in ("keep", "fix", "drop"))
            + f'</div></header>{it.get("info_html", "")}' + (f'<div class="figs">{figs}</div>' if figs else "") + (edit_html(it["edit"]) if it.get("edit") else "") +
            f'<div class="body"><div><h4>Look for</h4><ul class="checks">{checks}</ul></div>'
            f'<div><h4>Notes</h4><textarea class="notes" rows="4" placeholder="What to change, or what you noticed" aria-label="Notes for {H.escape(it["name"])}"></textarea>'
            f'<div class="nextrow"><button class="next" type="button">Save and next</button><span class="saved" aria-live="polite"></span></div></div></div></article>')


def build_html(title, intro, groups, collection="review", tally_words=("keep", "fix", "drop"), storage="asset-review-v1", page_title=None, after_html=""):
    n = sum(len(items) for _, items in groups)
    body = []
    for gt, items in groups:
        body.append(f'<section><h2>{H.escape(gt)}</h2>' + "".join(item_html(it) for it in items) + "</section>")
    ids = [it["id"] for _, items in groups for it in items]
    page = TEMPLATE
    for k, v in (("%%TITLE%%", H.escape(title)), ("%%INTRO%%", H.escape(intro)), ("%%BODY%%", "".join(body)), ("%%IDS%%", json.dumps(ids)), ("%%PAGETITLE%%", H.escape(page_title or title)), ("%%N%%", str(n)), ("%%COLL%%", collection), ("%%TALLY%%", json.dumps(list(tally_words))), ("%%STORE%%", storage), ("%%AFTER%%", after_html)):
        page = page.replace(k, v)
    return page


TEMPLATE = r"""<title>%%PAGETITLE%%</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Patrick+Hand&display=swap">
<style>
:root{--bg:#f6f5f1;--card:#ffffff;--fg:#1b1d22;--mute:#6b6f78;--line:#dcdad2;--accent:#2f4f7f;--keep:#2f7d4f;--fix:#b0701a;--drop:#b3402f;--keep-bg:#e3f1e8;--fix-bg:#f7ebd4;--drop-bg:#f6dfda;--plate:#ffffff;--bar:#ffffffee}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#15171b;--card:#1e2026;--fg:#e9e8e4;--mute:#a0a4ad;--line:#33363e;--accent:#8fb0e6;--keep:#6cc490;--fix:#e0a550;--drop:#ef8a78;--keep-bg:#1e3a2b;--fix-bg:#3d2f17;--drop-bg:#402420;--plate:#f6f5f1;--bar:#1e2026ee;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#15171b;--card:#1e2026;--fg:#e9e8e4;--mute:#a0a4ad;--line:#33363e;--accent:#8fb0e6;--keep:#6cc490;--fix:#e0a550;--drop:#ef8a78;--keep-bg:#1e3a2b;--fix-bg:#3d2f17;--drop-bg:#402420;--plate:#f6f5f1;--bar:#1e2026ee;color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font:15px/1.5 Inter,system-ui,sans-serif;padding-inline:max(16px,env(safe-area-inset-left,0px)) max(16px,env(safe-area-inset-right,0px));padding-block:0 48px}
main{max-width:980px;margin:0 auto}
h1,h2,h3{font-family:"Patrick Hand","Comic Sans MS",cursive;font-weight:400;text-wrap:balance;margin:0}
h1{font-size:2rem;margin-top:20px}
h2{font-size:1.5rem;margin:28px 0 12px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:1.35rem;display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
h4{margin:0 0 6px;font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;color:var(--mute);font-weight:600}
.intro{color:var(--mute);max-width:65ch;margin:6px 0 0}
.bar{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--bar);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);margin:0 calc(-1*max(16px,env(safe-area-inset-left,0px)));padding:8px max(16px,env(safe-area-inset-left,0px));display:flex;gap:12px;align-items:center;flex-wrap:wrap}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);background:var(--bar);z-index:10}
.prog{flex:1 1 220px;min-width:0}.prog b{font-variant-numeric:tabular-nums}
.meter{height:6px;border-radius:3px;background:var(--line);overflow:hidden;margin-top:4px;display:flex}
.meter i{display:block;height:100%}.meter .k{background:var(--keep)}.meter .f{background:var(--fix)}.meter .d{background:var(--drop)}
.filters{display:flex;gap:6px;flex-wrap:wrap}
.filters button{font:inherit;font-size:.8rem;padding:4px 10px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}
.filters button[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--bg)}
.banner{margin:12px 0;padding:10px 12px;border-radius:8px;background:var(--fix-bg);color:var(--fg);font-size:.9rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;margin:0 0 16px;scroll-margin-top:70px}
.card header{display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:10px}
.tag{font:600 .75rem Inter,sans-serif;letter-spacing:.05em;background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:1px 7px;color:var(--mute)}
.verdict{display:flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.verdict label{cursor:pointer;position:relative}.verdict input{position:absolute;inset:0;width:100%;height:100%;opacity:0;margin:0;cursor:pointer}
.verdict span{display:block;padding:7px 16px;font-weight:500;font-size:.9rem;border-left:1px solid var(--line);min-width:64px;text-align:center}
.verdict label:first-child span{border-left:0}
.verdict input:focus-visible+span{outline:2px solid var(--accent);outline-offset:-2px}
.verdict .v-keep input:checked+span{background:var(--keep-bg);color:var(--keep)}
.verdict .v-fix input:checked+span{background:var(--fix-bg);color:var(--fix)}
.verdict .v-drop input:checked+span{background:var(--drop-bg);color:var(--drop)}
.figs{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,330px),1fr));gap:12px}
figure{margin:0;min-width:0}.plate{background:var(--plate);border:1px solid var(--line);border-radius:8px;padding:4px}
.fig{display:block;width:100%;height:auto}
figcaption{font-size:.8rem;color:var(--mute);margin-top:4px}figcaption b{color:var(--fg)}
.body{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:14px}
.info{margin:0 0 4px;display:grid;gap:8px}.info p{margin:0}.info .claim{font-size:1rem}
.info blockquote{margin:0;padding:6px 10px;border-left:3px solid var(--accent);background:var(--bg);font-size:.9rem;overflow-wrap:anywhere}
.info .meta{font-size:.8rem;color:var(--mute)}
.info details{font-size:.85rem}.info summary{cursor:pointer;color:var(--mute)}.info details p{margin-top:6px;white-space:pre-wrap;overflow-wrap:anywhere;font-family:ui-monospace,monospace;font-size:.78rem;max-height:18em;overflow:auto}
.info mark{background:var(--fix-bg);color:var(--fg);padding:0 1px}
.joke-lines{font-family:"Patrick Hand","Comic Sans MS",cursive;font-size:1.15rem}
@media (max-width:680px){.body{grid-template-columns:1fr}}
.checks{list-style:none;margin:0;padding:0;display:grid;gap:6px}
.checks label{display:flex;gap:8px;align-items:flex-start;cursor:pointer}
.checks input{margin-top:4px;width:17px;height:17px;flex:none;accent-color:var(--accent)}
textarea{width:100%;font:inherit;color:var(--fg);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px;resize:vertical;min-width:0}
.saved{font-size:.75rem;color:var(--mute);min-height:1.2em;margin-top:4px}
.nextrow{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:8px}
.nextrow .saved{margin-top:0}
.next{font:inherit;font-weight:600;padding:6px 14px;border-radius:8px;border:1px solid var(--accent);background:transparent;color:var(--accent);cursor:pointer}
.next:hover,.next:focus-visible{background:var(--accent);color:var(--bg)}
.thanks{background:var(--keep-bg);border:2px solid var(--keep);border-radius:12px;padding:16px 20px;margin:12px 0 16px;scroll-margin-top:70px}
.thanks h2{margin:0 0 4px;color:var(--keep)}
.thanks p{margin:4px 0}
.thanks .mute{color:var(--mute);font-size:.85rem}
.edit{margin:10px 0 4px;border:1px dashed var(--line);border-radius:10px;padding:8px 12px}
.edit summary{cursor:pointer;font-weight:600;color:var(--accent)}
.card.edited .edit summary::after{content:" (changed)";color:var(--fix)}
.edit .meta{font-size:.8rem;color:var(--mute);margin:6px 0}
.fld{display:grid;gap:4px;margin:8px 0;font-size:.85rem;color:var(--mute)}
.erow{display:flex;gap:6px 14px;flex-wrap:wrap;align-items:center;margin:8px 0;font-size:.85rem;color:var(--mute)}
.erow b{color:var(--fg);min-width:4.5em}
.erow.line textarea{flex:1 1 18em;width:auto;min-width:0}
.erow label{display:inline-flex;gap:6px;align-items:center}
.erow select,.erow input[type=text]{font:inherit;color:var(--fg);background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:3px 6px;min-width:0;max-width:100%}
.comic{margin:16px 0 24px}
.comic h2{margin:0 0 6px}
.comic .pages{display:grid;gap:18px;justify-items:center}
.comic figure{margin:0;width:100%;max-width:760px}
.comic svg{width:100%;height:auto;display:block;border:1px solid var(--line);border-radius:6px;background:#fff}
.card.flash{outline:2px solid var(--accent);outline-offset:2px}
.card.done{border-left:4px solid var(--accent)}
.general{margin-top:28px}
.hide{display:none}
.submit{font:inherit;font-weight:600;padding:7px 16px;border-radius:8px;border:1px solid var(--accent);background:var(--accent);color:var(--bg);cursor:pointer}
.submit.big{padding:12px 28px;font-size:1rem}
.end{margin-top:24px;display:grid;gap:8px;justify-items:start}
</style>
<main>
<h1>%%TITLE%%</h1>
<p class="intro">%%INTRO%%</p>
<section id="thanks" class="thanks hide" role="status" tabindex="-1"><h2>Review submitted</h2><p id="thanks-sum"></p><p class="mute">Claude can now read your answers. You can keep editing and submit again.</p><button class="next" id="thanks-back" type="button">Back to the review</button></section>
%%AFTER%%
<div class="bar" role="region" aria-label="Progress">
  <div class="prog"><span><b id="done">0</b> of %%N%% judged</span> &middot; <span id="tally"></span><div class="meter" aria-hidden="true"><i class="k"></i><i class="f"></i><i class="d"></i></div></div>
  <div class="filters" role="group" aria-label="Filter"><button data-f="all" aria-pressed="true">All</button><button data-f="open" aria-pressed="false">To do</button><button data-f="fix" aria-pressed="false">Fix</button><button data-f="drop" aria-pressed="false">Drop</button></div>
  <button class="submit" type="button">Submit review</button>
</div>
<div id="banner" class="banner hide" role="status"></div>
%%BODY%%
<section class="end"><button class="submit big" type="button">Submit review</button><div class="saved" id="submit-note" aria-live="polite">Everything saves as you go. Submit tells Claude you are finished.</div></section>
<section class="general"><h2>Anything else</h2><textarea id="general" rows="4" placeholder="Anything not tied to one asset" aria-label="General notes"></textarea><div class="saved" id="general-saved" aria-live="polite"></div></section>
</main>
<script>
(function(){
  var IDS=%%IDS%%, LS="%%STORE%%", W=%%TALLY%%, state={}, db=null, timers={}, busy={}, dirty={}, pending={}, lastWritten={};
  function card(id){return document.getElementById("item-"+id)}
  function hasKeys(o){return !!o&&Object.keys(o).length>0}
  function readEdit(c){var e={},d=c.querySelector(".edit");if(!d)return e;
    var s=d.querySelector("[data-e=scene]");if(s&&s.value!==s.dataset.orig)e.scene=s.value;
    d.querySelectorAll("[data-line]").forEach(function(r){var o={},t=r.querySelector("[data-e=text]"),rm=r.querySelector("[data-e=remove]");
      if(t.value!==t.dataset.orig)o.text=t.value;if(rm.checked)o.remove=true;
      if(hasKeys(o)){(e.lines=e.lines||{})[r.dataset.line]=o}});
    var al=d.querySelector("[data-addline]");if(al){var sp=al.querySelector("[data-e=speaker]").value,tx=al.querySelector("[data-e=text]").value;if(sp&&tx.trim())e.add_lines=[{speaker:sp,text:tx}]}
    d.querySelectorAll("[data-char]").forEach(function(r){var o={};r.querySelectorAll("select").forEach(function(x){if(x.value!==x.dataset.orig)o[x.dataset.e]=x.value});
      if(hasKeys(o)){(e.chars=e.chars||{})[r.dataset.char]=o}});
    d.querySelectorAll("[data-prop]").forEach(function(r){var o={};r.querySelectorAll("[data-e]").forEach(function(x){var k=x.dataset.e;
      if(k==="remove"){if(x.checked)o.remove=true}else if(x.value!==x.dataset.orig)o[k]=x.value});
      if(hasKeys(o)){(e.props=e.props||{})[r.dataset.prop]=o}});
    var ap=d.querySelector("[data-addprop]");if(ap){var k=ap.querySelector("[data-e=kind]").value;if(k)e.add_props=[{kind:k,label:ap.querySelector("[data-e=label]").value}]}
    var ac=d.querySelector("[data-addchar]");if(ac){var i=ac.querySelector("[data-e=id]").value;if(i){var o2={id:i};ac.querySelectorAll("select").forEach(function(x){if(x.dataset.e!=="id"&&x.value)o2[x.dataset.e]=x.value});e.add_chars=[o2]}}
    return e}
  function paintEdit(c,e){e=e||{};var d=c.querySelector(".edit");if(!d)return;
    var s=d.querySelector("[data-e=scene]");if(s&&document.activeElement!==s)s.value=e.scene!=null?e.scene:s.dataset.orig;
    d.querySelectorAll("[data-line]").forEach(function(r){var o=(e.lines||{})[r.dataset.line]||{},t=r.querySelector("[data-e=text]");
      if(t!==document.activeElement)t.value=o.text!=null?o.text:t.dataset.orig;r.querySelector("[data-e=remove]").checked=!!o.remove});
    var al=d.querySelector("[data-addline]");if(al){var l0=(e.add_lines||[])[0]||{};al.querySelector("[data-e=speaker]").value=l0.speaker||"";if(al.querySelector("[data-e=text]")!==document.activeElement)al.querySelector("[data-e=text]").value=l0.text||""}
    d.querySelectorAll("[data-char]").forEach(function(r){var o=(e.chars||{})[r.dataset.char]||{};r.querySelectorAll("select").forEach(function(x){x.value=o[x.dataset.e]!=null?o[x.dataset.e]:x.dataset.orig})});
    d.querySelectorAll("[data-prop]").forEach(function(r){var o=(e.props||{})[r.dataset.prop]||{};r.querySelectorAll("[data-e]").forEach(function(x){var k=x.dataset.e;
      if(k==="remove")x.checked=!!o.remove;else if(x!==document.activeElement)x.value=o[k]!=null?o[k]:x.dataset.orig})});
    var ap=d.querySelector("[data-addprop]");if(ap){var a=(e.add_props||[])[0]||{};ap.querySelector("[data-e=kind]").value=a.kind||"";if(ap.querySelector("[data-e=label]")!==document.activeElement)ap.querySelector("[data-e=label]").value=a.label||""}
    var ac=d.querySelector("[data-addchar]");if(ac){var b=(e.add_chars||[])[0]||{};ac.querySelectorAll("select").forEach(function(x){x.value=b[x.dataset.e]||""})}
    if(hasKeys(e))d.open=true;c.classList.toggle("edited",hasKeys(e))}
  function read(id){var c=card(id),o={checks:{},notes:c.querySelector("textarea.notes").value,verdict:"",edit:readEdit(c)};
    c.querySelectorAll(".checks input").forEach(function(b){if(b.checked)o.checks[b.dataset.k]=true});
    var r=c.querySelector(".verdict input:checked");if(r)o.verdict=r.value;return o}
  function paint(id,o){var c=card(id);o=o||{};
    c.querySelectorAll(".checks input").forEach(function(b){b.checked=!!(o.checks&&o.checks[b.dataset.k])});
    c.querySelectorAll(".verdict input").forEach(function(r){r.checked=(r.value===o.verdict)});
    var t=c.querySelector("textarea.notes");if(document.activeElement!==t)t.value=o.notes||"";
    paintEdit(c,o.edit);
    c.classList.toggle("done",!!o.verdict)}
  function tally(){var k=0,f=0,d=0;IDS.forEach(function(id){var v=(state[id]||{}).verdict;if(v==="keep")k++;else if(v==="fix")f++;else if(v==="drop")d++});
    var n=IDS.length;document.getElementById("done").textContent=k+f+d;
    document.getElementById("tally").textContent=k+" "+W[0]+", "+f+" "+W[1]+", "+d+" "+W[2];
    var m=document.querySelectorAll(".meter i");m[0].style.width=100*k/n+"%";m[1].style.width=100*f/n+"%";m[2].style.width=100*d/n+"%";filter()}
  var cur="all";
  function filter(){IDS.forEach(function(id){var v=(state[id]||{}).verdict||"",show=cur==="all"||(cur==="open"&&!v)||cur===v;card(id).classList.toggle("hide",!show)})}
  document.querySelectorAll(".filters button").forEach(function(b){b.addEventListener("click",function(){cur=b.dataset.f;
    document.querySelectorAll(".filters button").forEach(function(x){x.setAttribute("aria-pressed",x===b)});filter()})});
  function stash(){try{localStorage.setItem(LS,JSON.stringify({s:state,g:document.getElementById("general").value}))}catch(e){}}
  function say(id,t){var el=id==="general"?document.getElementById("general-saved"):card(id).querySelector(".saved");el.textContent=t}
  function save(id){clearTimeout(timers[id]);timers[id]=setTimeout(function(){flush(id)},500)}
  function flush(id){
    if(!db){say(id,"Kept in this browser only");return}
    if(busy[id]){dirty[id]=true;return}
    busy[id]=true;pending[id]=false;
    var body=id==="general"?{notes:document.getElementById("general").value,updated:new Date().toISOString()}:Object.assign({},state[id],{item:id,updated:new Date().toISOString()});
    lastWritten[id]=body.updated;say(id,"Saving...");
    db.doc("%%COLL%%/"+id).set(body).then(function(){say(id,"Saved")},function(e){say(id,"Not saved: "+((e&&e.message)||"error"))}).then(function(){busy[id]=false;if(dirty[id]){dirty[id]=false;flush(id)}})}
  function changed(id){pending[id]=true;state[id]=read(id);card(id).classList.toggle("done",!!state[id].verdict);card(id).classList.toggle("edited",hasKeys(state[id].edit));tally();stash();save(id)}
  IDS.forEach(function(id){var c=card(id);c.addEventListener("change",function(){changed(id)});c.querySelector("textarea.notes").addEventListener("input",function(){changed(id)});
    c.querySelectorAll(".edit textarea,.edit input[type=text]").forEach(function(x){x.addEventListener("input",function(){changed(id)})})});
  function go(el){el.scrollIntoView({behavior:"smooth",block:"start"})}
  function nextFrom(id){var i=IDS.indexOf(id),order=IDS.slice(i+1).concat(IDS.slice(0,i));
    function open(x){return !card(x).classList.contains("hide")}
    for(var j=0;j<order.length;j++){if(open(order[j])&&!(state[order[j]]||{}).verdict)return order[j]}
    var after=IDS.slice(i+1).filter(open);return after.length?after[0]:null}
  IDS.forEach(function(id){var c=card(id),b=c.querySelector(".next");
    if(IDS.indexOf(id)===IDS.length-1)b.textContent="Save and finish";
    b.addEventListener("click",function(){
      state[id]=read(id);if(pending[id]){clearTimeout(timers[id]);flush(id)}
      var n=nextFrom(id);
      if(n){var t=card(n);go(t);t.classList.add("flash");setTimeout(function(){t.classList.remove("flash")},1200)}
      else{go(document.querySelector(".end"));setNote("All judged. Press Submit review when you are ready.")}})});
  var g=document.getElementById("general");g.addEventListener("input",function(){stash();save("general")});
  try{var old=JSON.parse(localStorage.getItem(LS)||"null");if(old){state=old.s||{};IDS.forEach(function(id){if(state[id])paint(id,state[id])});g.value=old.g||""}}catch(e){}
  tally();
  var banner=document.getElementById("banner");
  function show(t){banner.textContent=t;banner.classList.toggle("hide",!t)}
  var slow=setTimeout(function(){show("The saved answers can't be reached yet. What you enter is kept in this browser and saved when the connection returns.")},10000);
  function connect(){
    if(!(window.claude&&window.claude.use))return show("Answers are kept in this browser only; they are not shared with Claude.");
    window.claude.use("db").then(function(d){
      if(!d){clearTimeout(slow);return show("Answers are kept in this browser only (sign in to the artifact to save them where Claude can read them).")}
      db=d;
      db.collection("%%COLL%%").onSnapshot(function(snap){
        if(!snap.metadata.fromCache){clearTimeout(slow);show("")}
        snap.docs.forEach(function(s){var id=s.id,o=s.data();if(!o||(s.metadata&&s.metadata.hasPendingWrites))return;
          if(id==="general"){if(document.activeElement!==g)g.value=o.notes||"";return}
          if(IDS.indexOf(id)<0||busy[id]||dirty[id]||pending[id])return;if(o.updated&&lastWritten[id]&&o.updated<lastWritten[id])return;state[id]={checks:o.checks||{},notes:o.notes||"",verdict:o.verdict||"",edit:o.edit||{}};paint(id,state[id])});
        tally();
      },function(e){clearTimeout(slow);show("Saved answers could not be loaded ("+((e&&e.code)||"error")+"). What you enter is kept in this browser.")});
    },function(){clearTimeout(slow);show("Answers are kept in this browser only.")});
  }
  var armed=false,armTimer=null;
  function setBtn(t){document.querySelectorAll(".submit").forEach(function(b){b.textContent=t})}
  function setNote(t){document.getElementById("submit-note").textContent=t}
  function submitReview(){
    var k=0,f=0,d=0;IDS.forEach(function(id){var v=(state[id]||{}).verdict;if(v==="keep")k++;else if(v==="fix")f++;else if(v==="drop")d++});
    var un=IDS.length-k-f-d;
    if(un>0&&!armed){armed=true;setBtn(un+" not judged. Submit anyway?");clearTimeout(armTimer);armTimer=setTimeout(function(){armed=false;setBtn("Submit review")},5000);return}
    armed=false;clearTimeout(armTimer);
    IDS.forEach(function(id){if(pending[id])flush(id)});
    var body={at:new Date().toISOString(),keep:k,fix:f,drop:d,unjudged:un};
    var when=new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"}),sum=k+" "+W[0]+", "+f+" "+W[1]+", "+d+" "+W[2]+", "+un+" not judged";
    if(!db){setNote("Not submitted: answers are only in this browser, so Claude cannot see them.");return}
    setNote("Submitting...");
    db.doc("%%COLL%%/_submitted").set(body).then(function(){setNote("Submitted at "+when+" ("+sum+"). You can still change answers and submit again.");setBtn("Submit again");
      var t=document.getElementById("thanks");document.getElementById("thanks-sum").textContent="Submitted at "+when+": "+sum+".";t.classList.remove("hide");var cm=document.getElementById("comic");if(cm)cm.classList.remove("hide");go(t);t.focus({preventScroll:true})},function(e){setNote("Not submitted: "+((e&&e.message)||"error"))})}
  document.querySelectorAll(".submit").forEach(function(b){b.addEventListener("click",submitReview)});
  document.getElementById("thanks-back").addEventListener("click",function(){document.getElementById("thanks").classList.add("hide");var cm=document.getElementById("comic");if(cm)cm.classList.add("hide");var n=IDS.filter(function(x){return !(state[x]||{}).verdict})[0];go(n?card(n):document.querySelector("main"))});
  connect();
})();
</script>
"""
