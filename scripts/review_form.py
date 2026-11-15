#!/usr/bin/env python3
"""Build a review form as one self-contained web page, for any checklist of things to look at and judge.

A page made here shows, for each item, its pictures, a list of things to check, a keep / fix / drop verdict and a notes box, and saves
each answer as it is given. Published as an Artifact with the `db` capability, the answers are stored in the artifact's database under the
collection `review` (one document per item id, plus `review/general`), where Claude can read them back with the ArtifactData tool.
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


def item_html(it):
    figs = "".join(f'<figure><div class="plate">{v["svg"]}</div><figcaption><b>{H.escape(v["id"])}</b> {H.escape(v["label"])}</figcaption></figure>' for v in it["variants"])
    checks = "".join(f'<li><label><input type="checkbox" data-k="{i}"> <span>{H.escape(c)}</span></label></li>' for i, c in enumerate(it["checks"]))
    return (f'<article class="card" id="item-{H.escape(it["id"])}" data-id="{H.escape(it["id"])}">'
            f'<header><h3><span class="tag">{H.escape(it["id"])}</span> {H.escape(it["name"])}</h3>'
            f'<div class="verdict" role="radiogroup" aria-label="Verdict for {H.escape(it["name"])}">'
            + "".join(f'<label class="v-{v}"><input type="radio" name="v-{H.escape(it["id"])}" value="{v}"><span>{v.title()}</span></label>' for v in ("keep", "fix", "drop"))
            + f'</div></header><div class="figs">{figs}</div>'
            f'<div class="body"><div><h4>Look for</h4><ul class="checks">{checks}</ul></div>'
            f'<div><h4>Notes</h4><textarea rows="4" placeholder="What to change, or what you noticed" aria-label="Notes for {H.escape(it["name"])}"></textarea>'
            f'<div class="saved" aria-live="polite"></div></div></div></article>')


def build_html(title, intro, groups):
    n = sum(len(items) for _, items in groups)
    body = []
    for gt, items in groups:
        body.append(f'<section><h2>{H.escape(gt)}</h2>' + "".join(item_html(it) for it in items) + "</section>")
    ids = [it["id"] for _, items in groups for it in items]
    page = TEMPLATE
    for k, v in (("%%TITLE%%", H.escape(title)), ("%%INTRO%%", H.escape(intro)), ("%%BODY%%", "".join(body)), ("%%IDS%%", json.dumps(ids)), ("%%N%%", str(n))):
        page = page.replace(k, v)
    return page


TEMPLATE = r"""<title>%%TITLE%%</title>
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
.verdict label{cursor:pointer}.verdict input{position:absolute;opacity:0;pointer-events:none}
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
@media (max-width:680px){.body{grid-template-columns:1fr}}
.checks{list-style:none;margin:0;padding:0;display:grid;gap:6px}
.checks label{display:flex;gap:8px;align-items:flex-start;cursor:pointer}
.checks input{margin-top:4px;width:17px;height:17px;flex:none;accent-color:var(--accent)}
textarea{width:100%;font:inherit;color:var(--fg);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px;resize:vertical;min-width:0}
.saved{font-size:.75rem;color:var(--mute);min-height:1.2em;margin-top:4px}
.card.done{border-left:4px solid var(--accent)}
.general{margin-top:28px}
.hide{display:none}
</style>
<main>
<h1>%%TITLE%%</h1>
<p class="intro">%%INTRO%%</p>
<div class="bar" role="region" aria-label="Progress">
  <div class="prog"><span><b id="done">0</b> of %%N%% judged</span> &middot; <span id="tally"></span><div class="meter" aria-hidden="true"><i class="k"></i><i class="f"></i><i class="d"></i></div></div>
  <div class="filters" role="group" aria-label="Filter"><button data-f="all" aria-pressed="true">All</button><button data-f="open" aria-pressed="false">To do</button><button data-f="fix" aria-pressed="false">Fix</button><button data-f="drop" aria-pressed="false">Drop</button></div>
</div>
<div id="banner" class="banner hide" role="status"></div>
%%BODY%%
<section class="general"><h2>Anything else</h2><textarea id="general" rows="4" placeholder="Anything not tied to one asset" aria-label="General notes"></textarea><div class="saved" id="general-saved" aria-live="polite"></div></section>
</main>
<script>
(function(){
  var IDS=%%IDS%%, LS="asset-review-v1", state={}, db=null, timers={}, busy={}, dirty={};
  function card(id){return document.getElementById("item-"+id)}
  function read(id){var c=card(id),o={checks:{},notes:c.querySelector("textarea").value,verdict:""};
    c.querySelectorAll(".checks input").forEach(function(b){if(b.checked)o.checks[b.dataset.k]=true});
    var r=c.querySelector(".verdict input:checked");if(r)o.verdict=r.value;return o}
  function paint(id,o){var c=card(id);o=o||{};
    c.querySelectorAll(".checks input").forEach(function(b){b.checked=!!(o.checks&&o.checks[b.dataset.k])});
    c.querySelectorAll(".verdict input").forEach(function(r){r.checked=(r.value===o.verdict)});
    var t=c.querySelector("textarea");if(document.activeElement!==t)t.value=o.notes||"";
    c.classList.toggle("done",!!o.verdict)}
  function tally(){var k=0,f=0,d=0;IDS.forEach(function(id){var v=(state[id]||{}).verdict;if(v==="keep")k++;else if(v==="fix")f++;else if(v==="drop")d++});
    var n=IDS.length;document.getElementById("done").textContent=k+f+d;
    document.getElementById("tally").textContent=k+" keep, "+f+" fix, "+d+" drop";
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
    busy[id]=true;
    var body=id==="general"?{notes:document.getElementById("general").value,updated:new Date().toISOString()}:Object.assign({},state[id],{item:id,updated:new Date().toISOString()});
    say(id,"Saving...");
    db.doc("review/"+id).set(body).then(function(){say(id,"Saved")},function(e){say(id,"Not saved: "+((e&&e.message)||"error"))}).then(function(){busy[id]=false;if(dirty[id]){dirty[id]=false;flush(id)}})}
  function changed(id){state[id]=read(id);card(id).classList.toggle("done",!!state[id].verdict);tally();stash();save(id)}
  IDS.forEach(function(id){var c=card(id);c.addEventListener("change",function(){changed(id)});c.querySelector("textarea").addEventListener("input",function(){changed(id)})});
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
      db.collection("review").onSnapshot(function(snap){
        if(!snap.metadata.fromCache){clearTimeout(slow);show("")}
        snap.docs.forEach(function(s){var id=s.id,o=s.data();if(!o||(s.metadata&&s.metadata.hasPendingWrites))return;
          if(id==="general"){if(document.activeElement!==g)g.value=o.notes||"";return}
          if(IDS.indexOf(id)<0||busy[id]||dirty[id])return;state[id]={checks:o.checks||{},notes:o.notes||"",verdict:o.verdict||""};paint(id,state[id])});
        tally();
      },function(e){clearTimeout(slow);show("Saved answers could not be loaded ("+((e&&e.code)||"error")+"). What you enter is kept in this browser.")});
    },function(){clearTimeout(slow);show("Answers are kept in this browser only.")});
  }
  connect();
})();
</script>
"""
