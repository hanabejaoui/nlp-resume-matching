#!/usr/bin/env python3
"""
CV Language Quality Scorer

- Cleans ligatures & copy/paste artifacts (ﬁ → fi, removes soft hyphens, zero-width spaces)
- Optionally unwraps line-break hyphenations (fast-\n evolving → fast-evolving)
- Builds an allow-list from spaCy NER/PROPN + installed libs
- Runs LanguageTool, filters cosmetic rules, pretty-prints errors with line/col + carets
"""

import sys
import re
import unicodedata
import pkg_resources
import language_tool_python
import spacy
from typing import Set, Tuple

# -------------------------- Config --------------------------

ERROR_WEIGHT = 5.0  # weight per error per 100 words

# Formatting/cosmetic rules to ignore
IGNORE_RULES = {
    "WHITESPACE_RULE",
    "COMMA_PARENTHESIS_WHITESPACE",
    "PUNCTUATION_PARAGRAPH_END",
    "UPPERCASE_SENTENCE_START",
    "HYPHENATION",
}

# Normalize ligatures and private-use fallbacks
LIG_MAP = {
    "\ufb00": "ff",  "\ufb01": "fi",  "\ufb02": "fl",
    "\ufb03": "ffi", "\ufb04": "ffl",
    "\uf001": "fi",  "\uf002": "fl",
}

UNWRAP_LINEBREAK_HYPHENS = True  # join words broken by a line-end hyphen

# -------------------------- NLP -----------------------------

nlp = spacy.load("en_core_web_sm")

def extract_entities(text: str) -> Set[str]:
    """Return NER entities, PROPN tokens, and ALL-CAPS acronyms (+ plural forms)."""
    doc = nlp(text)
    ents = {ent.text.strip() for ent in doc.ents if ent.text.strip()}
    props = {
        token.text.strip()
        for token in doc
        if token.pos_ == "PROPN"
        or (
            token.text.isalpha()
            and (token.text.isupper() or (token.text.endswith("s") and token.text[:-1].isupper()))
        )
    }
    return ents.union(props)

def get_installed_libraries() -> Set[str]:
    return {dist.project_name.lower() for dist in pkg_resources.working_set}

# -------------------------- Cleaning ------------------------

def normalize_text(s: str) -> str:
    """Fix ligatures & invisible chars; optionally unwrap line-break hyphenation."""
    # Unicode compatibility normalization
    s = unicodedata.normalize("NFKC", s)
    # Map private-use ligatures if any survived
    s = s.translate(str.maketrans(LIG_MAP))
    # Remove soft hyphen and zero-width chars / BOM
    s = (s.replace("\u00ad", "")
           .replace("\u200b", "")
           .replace("\ufeff", ""))

    if UNWRAP_LINEBREAK_HYPHENS:
        # Join words broken across lines with a hyphen at end-of-line
        # e.g. "fast-\nevolving" -> "fast-evolving"
        s = re.sub(r"(\w)-\s*\n(\w)", r"\1-\2", s)
    return s

def strip_noise(text: str) -> str:
    """Remove emails, URLs, phones, and drop lines without lowercase letters."""
    text = normalize_text(text)
    text = re.sub(r"\S+@\S+", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\+?\d[\d\-\s\(\)]{6,}\d", " ", text)
    lines = text.splitlines()
    return "\n".join([ln for ln in lines if re.search(r"[a-z]", ln)])

# -------------------------- Pretty Print --------------------

def _idx_to_line_col(text: str, idx: int) -> Tuple[int, int]:
    line = text.count("\n", 0, idx) + 1
    last_nl = text.rfind("\n", 0, idx)
    col = idx - (last_nl + 1) + 1
    return line, col

def pretty_print_errors(errors, text: str) -> None:
    import shutil, textwrap
    width = max(60, min(shutil.get_terminal_size((100, 20)).columns, 120))
    print("Errors found:\n")
    for i, (snippet, m) in enumerate(errors, 1):
        # Some LT backends use .offset/.errorLength; keep robust fallbacks
        offset = getattr(m, "offset", 0)
        err_len = getattr(m, "errorLength", 1) or 1
        rule_id = getattr(m, "ruleId", "<rule>")
        msg = getattr(m, "message", "")
        sugg_list = getattr(m, "replacements", []) or []
        suggestions = ", ".join(sugg_list[:5]) or "<none>"

        line, col = _idx_to_line_col(text, offset)
        print(f"[{i}] Line {line}, Col {col} — {rule_id}")

        # Full source line
        line_start = text.rfind("\n", 0, offset) + 1
        line_end = text.find("\n", offset)
        if line_end == -1:
            line_end = len(text)
        line_text = text[line_start:line_end].rstrip("\r\n")
        print("    " + line_text)

        # Caret underline under the span
        caret = " " * (offset - line_start) + "^" * max(1, err_len)
        print("    " + caret)

        # Message and suggestions
        print(textwrap.fill("    Message: " + msg, width))
        print("    Suggestions: " + suggestions)
        issue_type = getattr(m, "ruleIssueType", "")
        if issue_type:
            print(f"    Type: {issue_type}")
        print()

# -------------------------- Scoring ------------------------

def compute_language_score(text: str, allowed_lower: Set[str]) -> None:
    """Compute and print grammar errors, error density, and quality score."""
    tool = language_tool_python.LanguageTool("auto")
    raw_matches = tool.check(text)

    errors = []
    for m in raw_matches:
        if getattr(m, "ruleId", None) in IGNORE_RULES:
            continue

        # Extract snippet robustly
        offset = getattr(m, "offset", 0)
        err_len = getattr(m, "errorLength", 0) or 0
        if err_len:
            snippet = text[offset:offset + err_len].strip()
        else:
            snippet = getattr(m, "context", "").strip() or text[offset:offset + 40].strip()

        # Skip if snippet is in allow-list (case-insensitive)
        if snippet.lower() in allowed_lower:
            continue

        errors.append((snippet, m))

    # Sort errors by position in text (reading order)
    errors.sort(key=lambda x: getattr(x[1], "offset", 0))

    words = re.findall(r"\w+", text)
    wc = len(words)
    err_per_100 = (len(errors) / wc * 100) if wc else 0
    score = max(0.0, 100.0 - (ERROR_WEIGHT * err_per_100))

    print(f"Word Count:               {wc}")
    print(f"Grammar/Spelling Errors:  {len(errors)}")
    print(f"Errors per 100 words:     {err_per_100:.1f}")
    print(f"Language Quality Score:   {score:.1f}/100\n")

    if errors:
        pretty_print_errors(errors, text)

# -------------------------- CLI ----------------------------

def main(txt_path: str) -> None:
    try:
        raw = open(txt_path, "r", encoding="utf-8").read()
    except Exception as e:
        print(f"Error reading '{txt_path}': {e}")
        sys.exit(1)

    # Allow-list: NER + PROPN + installed libraries + manual acronyms
    allowed = extract_entities(raw)
    allowed_lower = {e.lower() for e in allowed}
    allowed_lower |= get_installed_libraries()
    allowed_lower |= {"yourTerm".lower(), "AnotherAcronym".lower()}

    clean = strip_noise(raw)
    compute_language_score(clean, allowed_lower)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python CV_Language_score.py path/to/resume.txt")
        sys.exit(1)
    main(sys.argv[1])
