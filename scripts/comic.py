"""Comic pipeline. Run from anywhere: python scripts/comic.py <project> <command> [ids…]

  estimate              how many images each stage will create (before you spend anything)
  sheets                character sheets (one per look) + location + prop sheets
  pages [ids…]          draw every missing page (or only the given ids); page `anchor` is the style reference
  proof [ids…]          crop every panel into <project>/proof/ + checklist.md — the AGENT opens the crops and checks the text
  redo  <ids…>          redraw pages that failed proofreading — at most ONCE per page (saves the user's image quota)
  cards                 part covers, "previously", "to be continued" cards — drawn with real fonts, text is always exact
  export                out/part_N/ numbered images (one social post per part) + out/<title>.pdf + out/<title>.cbz

Images, job ids and redo counts live in <project>/img/manifest.json: re-running never pays twice.
"""
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import FONTS, env, project, read_json, write_json  # noqa: E402
from prompts import LAYOUTS, character_sheet, location_sheet, look_sheet, page, prop_sheet  # noqa: E402
from panels import panels  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith("--")]
if len(args) < 2:
    sys.exit(__doc__)
P = project(args[0]); CMD = args[1]; IDS = args[2:]
C = read_json(P["comic"]); STYLE = C["visualStyle"]; LANG = C.get("language", "Vietnamese")
MP = P["img"] / "manifest.json"; MAN = read_json(MP, {})
LABELS = {"part": "PHẦN", "previously": "PHẦN TRƯỚC", "next": "CÒN TIẾP…", "end": "HẾT", "follow": "Theo dõi để đọc tiếp",
          "nextPart": "Phần {n}: {title}", "ask": "Bạn muốn đọc truyện nào tiếp theo?", **C.get("labels", {})}


def save(): write_json(MP, MAN)
def upd(k, e):
    if e is None: MAN.pop(k, None)
    else:
        if "path" in e: e = {**e, "path": Path(e["path"]).relative_to(P["root"]).as_posix()}
        MAN[k] = {**MAN.get(k, {}), **e}
    save()
def file(k): return P["root"] / MAN[k]["path"] if MAN.get(k, {}).get("path") else None
def have(k): f = file(k); return bool(f and f.exists())
def out_of(k): return P["img"] / f"{k.replace('@', '_')}.png"


def provider():
    name = (env("IMAGE_PROVIDER", "sangtao") or "sangtao").lower()
    if name == "sangtao":
        from providers import sangtao as p
    elif name == "openai":
        from providers import openai_images as p
    else:
        sys.exit(f"Unknown IMAGE_PROVIDER '{name}'")
    return p


def task(k, prompt, aspect, refs, force=False):
    t = {"key": k, "prompt": prompt, "aspect": aspect, "out": out_of(k),
         "refs": [{"url": MAN[r].get("url"), "path": str(file(r))} for r in refs]}
    if not force and MAN.get(k, {}).get("pending") and not have(k): t["job"] = MAN[k]["pending"]
    return t


def run(tasks):
    if not tasks: print("nothing to create"); return
    print(f"{len(tasks)} image(s)…", flush=True)
    done, failed = provider().generate_many(tasks, upd)
    print(f"done {len(done)}, failed {len(failed)}")
    for k, why in failed.items(): print(f"  ✗ {k}: {why}")


def ref_name(r):
    if "@" in r:
        ch, lk = r.split("@"); return f"{C['characters'][ch]['name']} ({lk})"
    return (C.get("locations", {}).get(r) or C.get("props", {}).get(r) or {"name": r})["name"]


def look_keys():
    for ck, c in C["characters"].items():
        for i, lk in enumerate(c["looks"]): yield ck, c, lk, i


def page_tasks(ids, force=False):
    anchor = C.get("anchor") if have(C.get("anchor", "")) else None
    tasks = []
    for pg in C["pages"]:
        k = pg["id"]
        if ids and k not in ids: continue
        if not ids and have(k): continue
        refs = list(pg.get("refs", []))
        missing = [r for r in refs if not have(r)]
        if missing: print(f"{k}: missing sheets {missing} — run `sheets` first"); continue
        if "panels" in pg and len(LAYOUTS[pg["layout"]][1]) != len(pg["panels"]):
            print(f"{k}: layout {pg['layout']} needs {len(LAYOUTS[pg['layout']][1])} panels, script has {len(pg['panels'])}"); continue
        legend = "; ".join(f"image {i + 1} = {ref_name(r)}" for i, r in enumerate(refs))
        if anchor and k not in (anchor, "cover"):
            refs.append(anchor)
            legend += f"; image {len(refs)} = an earlier page of THIS comic — match its art style, colors, lettering font and gutters (do NOT copy its content)"
        tasks.append(task(k, page(STYLE, LANG, pg, legend), C.get("aspectRatio", "9:16"), refs, force))
    return tasks


# ── commands ──────────────────────────────────────────────────────────────────
if CMD == "estimate":
    n_looks = sum(1 for _ in look_keys()); n_loc = len(C.get("locations", {})); n_prop = len(C.get("props", {}))
    n_pages = len(C["pages"])
    sheets_left = sum(1 for ck, c, lk, i in look_keys() if not have(f"{ck}@{lk}")) + \
        sum(1 for k in list(C.get("locations", {})) + list(C.get("props", {})) if not have(k))
    pages_left = sum(1 for pg in C["pages"] if not have(pg["id"]))
    print(f"sheets: {n_looks} looks + {n_loc} locations + {n_prop} props  ({sheets_left} still to create)")
    print(f"pages:  {n_pages}  ({pages_left} still to create)")
    print(f"→ about {sheets_left + pages_left} image(s) now, plus at most one redo per page that fails proofreading "
          f"(budget ≈ {sheets_left + round(pages_left * 1.3)} image(s))")

elif CMD == "sheets":
    first, rest = [], []
    for ck, c, lk, i in look_keys():
        k = f"{ck}@{lk}"
        if have(k): continue
        appearance = f"{c['appearance']} {c['looks'][lk]}"
        if i == 0: first.append(task(k, character_sheet(STYLE, c["name"], appearance), "16:9", []))
        else: rest.append((k, look_sheet(STYLE, c["name"], appearance), f"{ck}@{next(iter(c['looks']))}"))
    for k, a in C.get("locations", {}).items():
        if not have(k): first.append(task(k, location_sheet(STYLE, a["name"], a["description"]), "16:9", []))
    for k, a in C.get("props", {}).items():
        if not have(k): first.append(task(k, prop_sheet(STYLE, a["name"], a["description"]), "4:3", []))
    run(first)
    run([task(k, p, "16:9", [base]) for k, p, base in rest if have(base)])   # extra looks need the first look as reference

elif CMD == "pages":
    run(page_tasks(IDS))

elif CMD == "redo":
    if not IDS: sys.exit("redo needs page ids, e.g. redo 1-07 2-01")
    allowed = [k for k in IDS if MAN.get(k, {}).get("redo", 0) < 1 or "--allow-more" in sys.argv]
    for k in set(IDS) - set(allowed): print(f"{k}: already redrawn once — keeping it (pass --allow-more to override)")
    tasks = page_tasks(allowed, force=True)
    for k in allowed: MAN.setdefault(k, {})["redo"] = MAN.get(k, {}).get("redo", 0) + 1
    save(); run(tasks)

elif CMD == "proof":
    from PIL import Image
    lines = ["# Proofreading checklist", "",
             "Open each crop and compare the lettering with the expected text, character by character (diacritics!).",
             "Also check: right character / right outfit (look), nothing extra drawn (stray letters, other scripts).",
             "Punctuation differences are fine. List the page ids that FAIL, then run `redo <ids>` once.", ""]
    for pg in C["pages"]:
        k = pg["id"]
        if (IDS and k not in IDS) or not have(k): continue
        f = file(k); im = Image.open(f).convert("RGB"); W, H = im.size
        if "panels" not in pg:
            exp = re.findall(r'"([^"]+)"', pg.get("p", "")); crop = im.resize((W // 2, H // 2)); name = f"{k}_page.jpg"
            crop.save(P["proof"] / name, quality=88); lines += [f"## {k}", f"- `proof/{name}` → " + (" | ".join(f"«{e}»" for e in exp) or "(no text)"), ""]
            continue
        boxes = panels(f)
        if len(boxes) != len(pg["panels"]):
            lines.append(f"⚠ {k}: found {len(boxes)} panels, script has {len(pg['panels'])} — check the whole page")
            boxes = [{"x": 0, "y": 0, "w": 1, "h": 1}] * len(pg["panels"])
        lines.append(f"## {k}")
        for i, (b, txt) in enumerate(zip(boxes, pg["panels"])):
            exp = re.findall(r'"([^"]+)"', txt)
            crop = im.crop((int(b["x"] * W), int(b["y"] * H), int((b["x"] + b["w"]) * W), int((b["y"] + b["h"]) * H)))
            name = f"{k}_{i + 1}.jpg"; crop.save(P["proof"] / name, quality=90)
            who = ", ".join(sorted(set(re.findall(r"\(([a-z0-9_]+@[a-z0-9_]+)", txt)))) or "-"
            lines.append(f"- `proof/{name}` [{who}] → " + (" | ".join(f"«{e}»" for e in exp) or "(no text)"))
        lines.append("")
    (P["proof"] / "checklist.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {P['proof'] / 'checklist.md'}")

elif CMD == "cards":
    from cards import make_cards
    make_cards(C, LABELS, P, file)

elif CMD == "export":
    from PIL import Image
    story = [pg for pg in C["pages"] if pg["id"] != "cover"]
    parts = sorted({pg.get("part", 1) for pg in story})
    card = lambda name: P["img"] / f"{name}.png"
    title = re.sub(r'[\\/:*?"<>|]', "", C["title"]).strip() or "comic"
    for p in parts:
        seq = [card(f"card_cover_{p}")] + ([card(f"card_recap_{p}")] if p > 1 else []) + \
              [file(pg["id"]) for pg in story if pg.get("part", 1) == p and have(pg["id"])] + [card(f"card_end_{p}")]
        seq = [f for f in seq if f and f.exists()]
        d = P["out"] / f"part_{p}"; d.mkdir(exist_ok=True)
        for old in d.glob("*.jpg"): old.unlink()
        for i, f in enumerate(seq): Image.open(f).convert("RGB").save(d / f"{i:02d}_{f.stem}.jpg", quality=92)
        print(f"part {p}: {len(seq)} images → {d}")
    full = [file("cover")] + [file(pg["id"]) for pg in story if have(pg["id"])] + [card(f"card_end_{parts[-1]}")]
    full = [f for f in full if f and f.exists()]
    ims = [Image.open(f).convert("RGB") for f in full]
    ims[0].save(P["out"] / f"{title}.pdf", save_all=True, append_images=ims[1:], resolution=200)
    with zipfile.ZipFile(P["out"] / f"{title}.cbz", "w", zipfile.ZIP_STORED) as z:
        for i, im in enumerate(ims):
            tmp = P["out"] / "_tmp.jpg"; im.save(tmp, quality=92); z.write(tmp, f"{i:03d}.jpg")
        tmp.unlink()
    print(f"pdf + cbz: {len(ims)} pages → {P['out']}")

else:
    sys.exit(__doc__)
