#!/usr/bin/env python3
"""Generate a single self-contained HTML dashboard of every PhysiqAI test artifact
(morphs, 3D meshes, validation, face-lock, contact sheets) so they can be browsed,
filtered, compared, and zoomed in one place instead of opening files one by one.

Run:  spike/.venv/bin/python spike/dashboard.py   (or: bash spike/dash.sh)
Opens at: spike/output/dashboard.html
"""
import json, pathlib, html, datetime

OUT = pathlib.Path("/Users/brianzhang/Projects/PhysiqAI/spike/output")

def categorize(p: pathlib.Path) -> str:
    s = str(p).lower()
    if "facelock" in s: return "Face-lock (identity proof)"
    if "/morph/" in s and "compare" in s: return "Avatar morphs"
    if "/val/" in s and "3panel" in s: return "Validation vs real people"
    if "trackа" in s or "/tracka/" in s or "_compare" in s and "/bz_" in s: return "Avatar morphs"
    if "sam3d" in s or "viz" in s or "mesh" in s: return "3D body meshes"
    if any(k in s for k in ("contact","candidate","final10","split")): return "Contact sheets / sets"
    return "Other"

# Section display order
ORDER = ["Avatar morphs", "Face-lock (identity proof)", "Validation vs real people",
         "3D body meshes", "Contact sheets / sets", "Other"]

def collect():
    items = {}
    for p in sorted(OUT.rglob("*")):
        if p.suffix.lower() not in (".png", ".jpg", ".jpeg"): continue
        if p.name == "dashboard.html": continue
        cat = categorize(p)
        rel = p.relative_to(OUT).as_posix()
        meta = None
        side = p.with_suffix(".json")
        if side.exists():
            try:
                loaded = json.load(open(side))
                meta = loaded if isinstance(loaded, dict) else None
            except Exception: meta = None
        items.setdefault(cat, []).append({
            "rel": rel, "name": p.name,
            "mtime": p.stat().st_mtime, "meta": meta,
        })
    for cat in items: items[cat].sort(key=lambda x: -x["mtime"])
    return items

def card(it):
    m = it["meta"]
    if m:
        chips = "".join(f"<span class='chip'>{html.escape(str(k))}: {html.escape(str(v))}</span>"
                        for k, v in m.items() if k not in ("photo",))
        sub = f"<div class='meta'>{chips}</div>"
    else:
        sub = ""
    ts = datetime.datetime.fromtimestamp(it["mtime"]).strftime("%b %d %H:%M")
    return f"""<div class="card">
      <img loading="lazy" src="{html.escape(it['rel'])}" onclick="zoom('{html.escape(it['rel'])}')">
      <div class="cap"><b>{html.escape(it['name'])}</b><span class="ts">{ts}</span></div>
      {sub}
    </div>"""

def build():
    items = collect()
    total = sum(len(v) for v in items.values())
    cats = [c for c in ORDER if c in items] + [c for c in items if c not in ORDER]
    nav = "".join(f"<button class='tab' onclick=\"show('{html.escape(c)}')\">{html.escape(c)} "
                  f"<span class=n>{len(items[c])}</span></button>" for c in cats)
    nav = "<button class='tab active' onclick=\"show('all')\">All <span class=n>%d</span></button>" % total + nav
    secs = ""
    for c in cats:
        cards = "".join(card(it) for it in items[c])
        secs += f"<section data-cat='{html.escape(c)}'><h2>{html.escape(c)}</h2><div class='grid'>{cards}</div></section>"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    doc = f"""<!doctype html><html><head><meta charset=utf-8>
<title>PhysiqAI — Test Dashboard</title>
<style>
  body{{margin:0;background:#0d0f12;color:#e6e8ea;font:14px/1.4 -apple-system,Segoe UI,Roboto,sans-serif}}
  header{{position:sticky;top:0;background:#13161b;padding:14px 20px;border-bottom:1px solid #222;z-index:10}}
  header h1{{margin:0 0 8px;font-size:18px}} header .sub{{color:#8b949e;font-size:12px;margin-bottom:10px}}
  .tab{{background:#1c2128;color:#c9d1d9;border:1px solid #30363d;border-radius:20px;padding:6px 12px;
        margin:0 6px 6px 0;cursor:pointer;font-size:12px}}
  .tab.active{{background:#1f6feb;border-color:#1f6feb;color:#fff}} .tab .n{{opacity:.6;margin-left:4px}}
  section{{padding:16px 20px}} h2{{font-size:15px;color:#58a6ff;border-bottom:1px solid #21262d;padding-bottom:6px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}}
  .card{{background:#161b22;border:1px solid #21262d;border-radius:10px;overflow:hidden}}
  .card img{{width:100%;display:block;cursor:zoom-in;background:#000}}
  .cap{{padding:8px 10px;display:flex;justify-content:space-between;font-size:12px;color:#c9d1d9}}
  .cap .ts{{color:#6e7681}}
  .meta{{padding:0 10px 10px;display:flex;flex-wrap:wrap;gap:4px}}
  .chip{{background:#0d2a4d;color:#79c0ff;border-radius:6px;padding:2px 7px;font-size:11px}}
  #lb{{position:fixed;inset:0;background:rgba(0,0,0,.92);display:none;align-items:center;justify-content:center;z-index:99;cursor:zoom-out}}
  #lb img{{max-width:96vw;max-height:96vh}}
</style></head><body>
<header><h1>🪞 PhysiqAI — Test Dashboard</h1>
  <div class="sub">{total} artifacts · generated {now} · click any image to enlarge</div>
  <div>{nav}</div></header>
{secs}
<div id="lb" onclick="this.style.display='none'"><img id="lbimg"></div>
<script>
  function zoom(src){{document.getElementById('lbimg').src=src;document.getElementById('lb').style.display='flex';}}
  function show(cat){{
    document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
    event.target.closest('.tab').classList.add('active');
    document.querySelectorAll('section').forEach(s=>{{
      s.style.display=(cat==='all'||s.dataset.cat===cat)?'block':'none';}});
  }}
</script></body></html>"""
    dash = OUT / "dashboard.html"
    dash.write_text(doc)
    print(f"dashboard: {total} artifacts across {len(cats)} sections -> {dash}")
    return dash

if __name__ == "__main__":
    build()
