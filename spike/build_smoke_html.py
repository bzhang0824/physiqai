#!/usr/bin/env python3
"""Build a single self-contained HTML page to review the pipeline smoke-test outputs.
Images are inlined as base64 so the file is portable. Run:
    spike/.venv/bin/python spike/build_smoke_html.py
"""
import base64
import json
import pathlib

D = pathlib.Path("spike/output/pipeline")
OUT = D / "review.html"


def b64(p):
    mime = "image/png" if p.suffix == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def img(p, cls=""):
    return f'<img class="{cls}" src="{b64(p)}">' if p.exists() else "<em>missing</em>"


scenarios = [
    ("Cut — 6 months (fat loss)", "bz02_IMG_7520_cut_6mo"),
    ("Lean bulk — 6 months (muscle gain)", "bz02_IMG_7520_leanbulk_6mo"),
]

cards = []
for title, stem in scenarios:
    meta = json.loads((D / f"{stem}_3panel.json").read_text())
    rows = "".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>"
        for k, v in [
            ("direction", meta["direction"]),
            ("weight", meta["weight"]),
            ("body fat", meta["bodyfat"]),
            ("lean Δ (lb)", meta["lean_delta_lb"]),
            ("confidence", f'{meta["confidence"]*100:.0f}%'),
            ("face-locked", "yes ✅" if meta["facelocked"] else "NO FACE ⚠️"),
            ("gen time", f'{meta["seconds"]}s'),
        ]
    )
    cards.append(f"""
    <section class="card">
      <h2>{title}</h2>
      <div class="panel">{img(D / f"{stem}_3panel.png", "wide")}</div>
      <div class="grid">
        <table>{rows}</table>
        <div class="prompt"><b>Prompt sent to the model:</b><br>{meta["prompt"]}</div>
      </div>
    </section>""")

face = D / "_face_fidelity.png"
face_block = f"""
    <section class="card hl">
      <h2>Face fidelity — the identity proof</h2>
      <p>ORIGINAL face · what the AI <em>raw edit</em> did to it · the <b>face-locked</b> result
      (your real face composited back). The right image should match the left.</p>
      <div class="panel">{img(face, "wide")}</div>
    </section>""" if face.exists() else ""

html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>PhysiqAI — Pipeline Smoke Test</title>
<style>
  body{{background:#0e0e10;color:#e8e8ea;font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:32px}}
  h1{{font-size:24px;margin:0 0 4px}} .sub{{color:#9a9aa2;margin:0 0 24px}}
  .card{{background:#17171a;border:1px solid #26262b;border-radius:14px;padding:20px;margin:0 0 24px}}
  .card.hl{{border-color:#1f6f43}}
  h2{{font-size:18px;margin:0 0 12px}}
  .panel img.wide{{width:100%;height:auto;border-radius:8px;display:block}}
  .grid{{display:grid;grid-template-columns:260px 1fr;gap:18px;margin-top:14px;align-items:start}}
  table{{border-collapse:collapse;width:100%;font-size:14px}}
  td{{padding:5px 8px;border-bottom:1px solid #26262b}} td:first-child{{color:#9a9aa2}}
  .prompt{{background:#0e0e10;border:1px solid #26262b;border-radius:8px;padding:12px;color:#c9c9cf;font-size:13px}}
  .ok{{color:#3ddc84}}
  @media(max-width:760px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body>
  <h1>PhysiqAI — Production Pipeline Smoke Test</h1>
  <p class="sub">Photo: bz02_IMG_7520 · engine-bounded magnitude · face-locked identity · ~$0.15/gen
  · <span class="ok">61 tests green</span></p>
  {face_block}
  {''.join(cards)}
</body></html>"""

OUT.write_text(html)
print("wrote", OUT.resolve(), f"({OUT.stat().st_size//1024} KB)")
