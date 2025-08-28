#!/usr/bin/env python3
"""
cv_presentation_score.py

Evaluates the “presentation” quality of a PDF resume across five dimensions:
 1. Typography           (fonts & sizes)
 2. Layout & Readability (margins & whitespace)
 3. Consistency          (bullet/date styles)
 4. Page Length
 5. ATS Friendliness

Each dimension is scored 0–5; summed → 0–25 → scaled to 0–100.

Usage:
    python CV_presentation_score.py path/to/resume.pdf
"""
import sys
import re
# Force UTF-8 encoding on Windows consoles (so emojis & dashes don’t crash)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import fitz            # PyMuPDF
import pdfplumber
import numpy as np

# Suggestions per dimension & score
SUGGESTIONS = {
    "Typography": {
        0: "❌ No approved fonts/sizes found. Switch to Arial/Calibri/Times New Roman at 10–12 pt body, 14–16 pt headings.",
        1: "⚠️ Most text uses unapproved fonts or sizes. Check your font choices and sizes.",
        2: "⚠️ Several spans outside approved size range. Make body text 10–12 pt, headings 14–16 pt.",
        3: "✅ Good, but a few small font inconsistencies remain.",
        4: "✅ Almost perfect—only minor font/style variations.",
        5: "🌟 Excellent—only approved fonts & sizes detected.",
    },
    "Layout": {
        0: "❌ Margins too tight and page too dense. Use ≥0.5 in margins and add whitespace.",
        1: "⚠️ Margins or whitespace far from ideal. Increase page padding.",
        2: "⚠️ Margins pass, but whitespace ratio low. Aim for ~50% white space.",
        3: "✅ Margins OK, whitespace could be a bit more generous.",
        4: "✅ Good balance of text & white space.",
        5: "🌟 Perfect margins & whitespace.",
    },
    "Consistency": {
        0: "❌ Mixed bullet styles and date formats. Pick one bullet and use en-dash for dates.",
        1: "⚠️ Multiple inconsistencies. Standardize bullets (`-` or `•`) and date separators (–).",
        2: "⚠️ Some inconsistencies in bullets or dates remain.",
        3: "✅ Consistency mostly good, minor mixing of bullet/type.",
        4: "🌟 Very consistent—only one minor deviation.",
        5: "🌟 Perfectly consistent bullets & dates.",
    },
    "PageLength": {
        0: "❌ Wrong page count. Aim for 1 page (<8 y exp) or 2 pages (>8 y exp).",
        3: "✅ Two pages OK based on experience length.",
        5: "🌟 Perfect page length.",
    },
    "ATS": {
        0: "❌ Contains images or special formatting that break ATS parsing.",
        1: "⚠️ Some unusual symbols detected; may confuse ATS.",
        3: "✅ Mostly ATS-friendly; double-check no hidden graphics.",
        5: "🌟 Fully ATS-compliant—plain text, no images.",
    }
}

# Typography settings
ALLOWED_FONTS = {
    "Arial", "Calibri", "Times New Roman", "Georgia", "Helvetica", "Cambria", "Verdana",
    "TimesNRMTPro", "TimesNRMTPro-SemiBold", "TimesNRMTPro-Bold",
}
BODY_SIZE_RANGE    = (10, 12)
HEADING_SIZE_RANGE = (14, 16)

# Layout settings
MIN_MARGIN_INCH = 0.5  # inches


def score_typography(doc):
    spans = []
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    font = span["font"].split("+")[-1]
                    size = round(span["size"])
                    spans.append((font, size))

    total = len(spans)
    if total == 0:
        return 0

    bad = sum(
        1
        for font, size in spans
        if font not in ALLOWED_FONTS
        or size < BODY_SIZE_RANGE[0]
        or size > HEADING_SIZE_RANGE[1]
    )
    return max(0, round((1 - bad / total) * 5))


def score_layout_whitespace(pdf):
    page = pdf.pages[0]
    w, h = page.width, page.height
    min_pts = MIN_MARGIN_INCH * 72

    words = page.extract_words()
    if not words:
        return 0

    x0 = min(wb["x0"] for wb in words)
    x1 = max(wb["x1"] for wb in words)
    y0 = min(wb["top"] for wb in words)
    y1 = max(wb["bottom"] for wb in words)

    margins_ok = (
        x0 >= min_pts and (w - x1) >= min_pts
        and y0 >= min_pts and (h - y1) >= min_pts
    )

    img = page.to_image(resolution=72).original.convert("L")
    arr = np.array(img)
    ws_ratio = np.mean(arr > 250)

    score = 3 if margins_ok else 0
    bonus = (ws_ratio - 0.3) / 0.4 * 2
    score += int(max(0, min(2, bonus)))
    return score


def score_consistency(text):
    bullets = re.findall(r"^[-•]\s", text, re.MULTILINE)
    types   = {b[0] for b in bullets}
    bscore  = 5 if len(types) <= 1 else max(0, 5 - len(types))

    dash = bool(re.search(r"\d{4}\s*–\s*\d{4}", text))
    hypo = bool(re.search(r"\d{4}\s*-\s*\d{4}", text))
    dscore = 5 if dash and not hypo else 3 if dash else 1

    return round((bscore + dscore) / 2)


def score_page_length(doc):
    n = len(doc)
    return 5 if n == 1 else 3 if n == 2 else 0


def score_ats_friendly(text):
    if "<img" in text or re.search(r"https?://\S+\.(png|jpg|svg)", text):
        return 0
    return 5


def presentation_score(pdf_path):
    doc  = fitz.open(pdf_path)
    pdfp = pdfplumber.open(pdf_path)
    raw  = "\n".join(p.extract_text() or "" for p in pdfp.pages)

    scores = {
        "Typography":  score_typography(doc),
        "Layout":      score_layout_whitespace(pdfp),
        "Consistency": score_consistency(raw),
        "PageLength":  score_page_length(doc),
        "ATS":         score_ats_friendly(raw),
    }

    print("Presentation dimension scores & suggestions:\n")
    for dim, sc in scores.items():
        sug = SUGGESTIONS[dim].get(sc, "")
        print(f"• {dim:12}: {sc}/5   {sug}")

    total  = sum(scores.values())
    scaled = round(total / 25 * 100, 1)
    print(f"\n Presentation Score: {scaled}/100")
    return scaled


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python CV_presentation_score.py path/to/resume.pdf")
        sys.exit(1)
    presentation_score(sys.argv[1])
