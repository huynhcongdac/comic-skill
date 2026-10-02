---
name: comic
description: Turn a story idea, a script or a full public-domain story into a multi-page comic (webtoon/manhwa style, 9:16 phone pages) with consistent characters, multiple outfits ("looks") per character, speech bubbles lettered in the target language, split into parts for TikTok/Facebook carousels, plus PDF/CBZ. Use when the user asks for a comic, truyện tranh, manga/manhwa/webtoon pages, or a comic series from a story.
---

# Comic skill

You (the agent) write the script, run the scripts, **look at every page yourself** and fix problems.
Images come from an image API (sangtao.ai by default — about 100–400 VND per image depending on the plan,
up to 20 reference images per image; OpenAI Images also works).

## 0. Setup (once)

```bash
pip install pillow numpy
cp .env.example .env          # then fill in SANGTAO_API_KEY (or OPENAI_API_KEY + IMAGE_PROVIDER=openai)
```
Ask the user for the key if `.env` is missing. Never print or commit it. A sangtao.ai key needs an image plan or
credit (no free tier on the API): https://sangtao.ai/vi/imagine?tab=pricing · docs: https://sangtao.ai/vi/api-docs/chatgpt-image.
Comics look best at `SANGTAO_RESOLUTION=2K`.

## 1. Write the script → `<project>/comic.json`

Ask the user for: the story (idea, script or full text), language of the lettering, art style, how long.
**If it is someone else's copyrighted story, stop**: only the user's own story, public-domain works, or works they may adapt.
Retell public-domain stories in your own words — translations have their own copyright.

**Plan by story beats, not by a page count.** List every beat first (setup, motive, warnings ignored, reveal, cost,
resolution, closing line). Give each beat 1–2 pages, add establishing panels when the place changes and reaction
panels after every shock. A short story needs ~25–30 pages; never squeeze a story into a few pages — that is what makes
comics feel abrupt. **Split into parts of 8–10 pages**, each ending on a cliffhanger (one social post per part).

Copy `examples/hoa-bi/comic.json` and keep its structure:

```jsonc
{
  "title": "HỌA BÌ", "language": "Vietnamese", "aspectRatio": "9:16",
  "visualStyle": "Chinese manhua horror comic art, ink lines, flat muted colors… NOT photorealistic",   // ONE style for everything
  "anchor": "1-01",                       // first approved page = style reference for every later page
  "characters": {
    "vuong": { "name": "Vương sinh",
      "appearance": "Chinese man aged 30. BODY: … FACE: … HAIR: …",          // English, no outfit here
      "looks": { "day": "OUTFIT: pale blue scholar robe…", "night": "OUTFIT: white sleeping robe…" } }   // ≥1 look
  },
  "locations": { "thuphong": { "name": "Thư phòng", "description": "English description" } },
  "props":     { "phattran": { "name": "Phất trần", "description": "English description" } },
  "parts": { "1": { "title": "Người đẹp trong sương", "recap": ["1-03", "1-09"], "summary": "1–2 sentences", "endBg": "1-09" } },
  "pages": [
    { "id": "cover", "refs": ["nang@beauty"], "p": "A comic BOOK COVER … Big title lettering: \"HỌA BÌ\" …" },
    { "id": "1-01", "part": 1, "layout": "1-2", "refs": ["vuong@day", "nang@beauty", "duong"],
      "panels": [ "Wide: misty road at dawn. Caption box: \"Thái Nguyên, một buổi sớm sương mù.\"",
                  "Vương sinh (vuong@day) notices a lone young woman (nang@beauty) ahead.",
                  "Vương sinh speaks. Speech bubble: \"Cô nương đi đâu sớm vậy?\"" ] }
  ]
}
```

Rules that matter:
- **Looks**: a character can have several outfits/forms (`doctor`, `casual`, `demon`…). Write `name (char@look)` in a panel
  and list `char@look` in the page `refs`. The first look is drawn from the description; later looks reuse the first
  look's sheet as reference, so the face stays identical.
- **refs**: every look / location / prop that appears on the page (max ~19 — the anchor page takes one slot).
- **Layout** (panel count must match): `1-2` `2-1` `2x2` `1-2-big` `big-2` `2-big` `1-big-1` `tall+2` `splash` `1-1-1`.
  Wide = establishing; split = dialogue/reaction; tall = full body/action; `big`/`splash` = the reveal. Max 4 panels per page.
- **Lettering**: put every bubble/caption/sound effect in double quotes. ≤ 12 words per bubble, ≤ 3 bubbles per panel.
  If a word keeps coming out wrong, rephrase the line instead of redrawing again.
- Describe panels in English (scene, camera, emotion); only the quoted text is in the target language.
- No gore: imply violence (silhouettes, aftermath). Stylized art passes content filters more easily than photos;
  rephrase if a page is refused.

Show the user the beat list and page count before generating. Then run `estimate` and tell them roughly how many images it will use.

## 2. Generate

```bash
python scripts/comic.py <project> estimate
python scripts/comic.py <project> sheets            # look at the sheets: same face across looks?
python scripts/comic.py <project> pages cover 1-01  # approve the anchor page (style, text size) before the rest
python scripts/comic.py <project> pages             # all remaining pages
```
Re-running never pays twice: job ids are saved immediately and resumed.

## 3. Proofread — you do it, with your own eyes

```bash
python scripts/comic.py <project> proof             # crops every panel into proof/ + proof/checklist.md
```
Open `proof/checklist.md`, then open **each crop image** and compare the drawn text with the expected text character by
character (tone marks!). Also check the right character/outfit is in the panel and nothing extra is drawn
(stray letters, another script). Ignore punctuation differences and tiny glitches a reader would not notice.

```bash
python scripts/comic.py <project> redo 1-07 2-01    # failed pages only — each page is redrawn AT MOST ONCE
```
Proofread the redrawn pages once more and accept them. Do not loop: the user pays per image.

## 4. Export

```bash
python scripts/comic.py <project> cards     # part covers, "previously…", "to be continued" / "the end" (exact text)
python scripts/comic.py <project> export    # out/part_N/ (numbered, one post per part) + out/<title>.pdf + .cbz
```
TikTok photo posts take up to 35 images (best 5–10); Instagram carousels up to 20. Tell the user where the files are.
