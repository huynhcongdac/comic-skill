"""Prompt templates: reference sheets + comic pages."""

# ── Reference sheets ──────────────────────────────────────────────────────────
# Multi-panel sheets give the model every angle of a character / place / object, so later pages stay consistent.

def character_sheet(style, name, appearance):
    return (f"Style: {style}\n"
            f"Character design sheet: Name: {name}. {appearance}\n"
            "Format: 16:9 landscape, four-panel layout. Left panel (largest, ~40% width): chest-up close-up portrait, "
            "high detail, clearly showing face, hairstyle, accessories and upper outfit. Right side (3 panels, ~20% width each): "
            "three full-body views — front, three-quarter, and back, static A-pose, complete figure head to toe.\n"
            "BACKGROUND: pure white, completely empty. No scenery. The character must look identical across all four panels.\n"
            "NO text, NO labels, NO captions, NO logos, NO watermarks.")


def look_sheet(style, name, appearance):
    """A second outfit / form of a character: drawn with the first look's sheet as the reference image."""
    return (character_sheet(style, name, appearance) +
            f"\nThe reference image is the SAME character ({name}). Keep the face, hair, body and proportions IDENTICAL — "
            "change ONLY the outfit / appearance described above.")


def location_sheet(style, name, description):
    return (f"Style: {style}\n"
            f"Location concept design sheet: Name: {name}. {description}.\n"
            "Format: 16:9 landscape, at least 4 panels showing the SAME location from different camera angles: wide "
            "establishing shot, reverse angle, overhead view, and a detail close-up.\n"
            "No characters or people. Consistent layout across panels. No text, labels, arrows or watermarks.")


def prop_sheet(style, name, description):
    return (f"Style: {style}\n"
            f"Prop design sheet: Name: {name}. {description}.\n"
            "Format: 4:3 landscape. One large main view plus front, side and back views of the same prop. Pure white background.\n"
            "No text, no dimension lines, no characters, no watermark.")


# ── Page layouts (9:16) ───────────────────────────────────────────────────────
# Choose by story rhythm: wide = establishing, split = dialogue / reaction, tall = full body / action,
# big / splash = the reveal. Max 4 panels per page; no panel flatter than ~2:1.
LAYOUTS = {
    "1-1-1":   ("three full-width rows of about equal height.", ["top row, full width", "middle row, full width", "bottom row, full width"]),
    "1-2":     ("top row one full-width panel (about 40% of the page height); bottom row split into two side-by-side panels (about 60%).",
                ["top, full width", "bottom left", "bottom right"]),
    "2-1":     ("top row split into two side-by-side panels (about 45% of the page height); bottom row one full-width panel (about 55%).",
                ["top left", "top right", "bottom, full width"]),
    "2x2":     ("a 2x2 grid: two rows, each split into two side-by-side panels of equal size.", ["top left", "top right", "bottom left", "bottom right"]),
    "1-2-big": ("row 1 one full-width panel (about 20% of the page height); row 2 split into two side-by-side panels (about 28%); "
                "row 3 one BIG full-width panel (about 52% of the page height) — the dramatic moment.",
                ["row 1, full width", "row 2 left", "row 2 right", "row 3, BIG full-width panel"]),
    "big-2":   ("top: one BIG full-width panel (about 55% of the page height); bottom row split into two side-by-side panels (about 45%).",
                ["top, BIG full-width panel", "bottom left", "bottom right"]),
    "2-big":   ("top row split into two side-by-side panels (about 40% of the page height); bottom: one BIG full-width panel (about 60%) — the dramatic moment.",
                ["top left", "top right", "bottom, BIG full-width panel"]),
    "1-big-1": ("row 1 one full-width panel (about 22%); row 2 one BIG full-width panel (about 50%) — the dramatic moment; row 3 one full-width panel (about 28%).",
                ["row 1, full width", "row 2, BIG full-width panel", "row 3, full width"]),
    "tall+2":  ("left column one TALL panel spanning the full page height (about 50% of the width); right column two panels stacked vertically.",
                ["left, tall full-height panel", "right top", "right bottom"]),
    "splash":  ("ONE single panel filling the whole page (splash page).", ["the whole page"]),
}


LETTERING = ("LETTERING: all text in {lang}, copied EXACTLY character by character from inside the quotes — double-check every "
             "diacritic / tone mark; never substitute a similar-looking word. Clean comic font, speech bubbles white with black text, "
             "caption boxes rectangular. No other text, no page numbers, no watermark, no signature.\n"
             "READABLE ON A PHONE: large bold lettering — the height of each text line about 1/25 of the page WIDTH; caption boxes use "
             "the SAME large bold size as speech bubbles; generous padding; high contrast.\n"
             "SAFE ZONE: keep every bubble, caption and sound effect out of the bottom 18% and the right 12% of the page "
             "(covered by app buttons on TikTok); artwork may extend there.")


def page(style, lang, page_spec, legend):
    """page_spec: {"layout", "panels": [...]} or {"p": free prompt (cover)}; legend: text mapping reference images."""
    if "panels" in page_spec:
        grid, cells = LAYOUTS[page_spec["layout"]]
        body = (f"A full comic book page, vertical 9:16, exactly {len(cells)} panels separated by thick WHITE gutters. "
                f"PAGE LAYOUT: {grid} No panel may be wider than 2:1. Reading order: left to right, top to bottom.\n" +
                "\n".join(f"Panel {i + 1} ({cells[i]}): {t}" for i, t in enumerate(page_spec["panels"])))
    else:
        body = page_spec["p"]
    return (f"{body}\nArt style: {style}\nReference images: {legend}. Characters must match their reference sheets exactly "
            "(same face, hair, outfit). Tags in parentheses like (minh@doctor) only say which reference to follow — never draw them.\n"
            + LETTERING.format(lang=lang))
