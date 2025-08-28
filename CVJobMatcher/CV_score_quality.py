#!/usr/bin/env python3
"""
CV Score Quality Orchestrator

This script runs three separate scoring modules on a PDF resume and
aggregates their results into a final weighted quality score (0–100).

Steps:
1. Structure Check (50%)
   • Calls CV_scoring_structure.py to verify essential sections (email, education, experience, skills).
   • Parses the “Structure Score” percentage from its output.

2. Text Preparation
   • Calls data_preparation_CV.py to extract text from PDF and clean it into resume.txt.

3. Language Quality (40%)
   • Runs CV_Language_score.py on the cleaned text to compute grammar/spelling error density and score.
   • Parses the “Language Quality Score” percentage from its output.

4. Presentation Quality (10%)
   • Runs CV_presentation_scoring.py on the original PDF to assess typography, layout, consistency, page length, and ATS-friendliness.
   • Parses the “Presentation Score” percentage from its output.

5. Aggregation
   • Combines the three component percentages with weights:
       Structure × 0.5 + Language × 0.4 + Presentation × 0.1
   • Prints each component’s score and the final overall CV Quality Score.

Usage:
    python CV_score_quality.py path/to/resume.pdf
"""
import sys
import subprocess
import os

# ─────────────────────────────────────────────────────────────────────────────
# Force UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
PY = sys.executable  # ensure we invoke the same Python interpreter
# ─────────────────────────────────────────────────────────────────────────────

def run(cmd):
    """Run subprocess.check_output with UTF-8 decoding and error replacement."""
    return subprocess.check_output(
        cmd,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

def safe_run(cmd):
    """
    Execute a command list, return (success: bool, stdout_or_error: str).
    """
    try:
        return True, run(cmd)
    except subprocess.CalledProcessError as e:
        return False, e.output or str(e)

def extract_pct(output: str, marker: str) -> float:
    """
    Scan each line of 'output' for 'marker' and parse the trailing percentage.
    Supports values like '100.0%' or '98.6/100'.
    """
    for line in output.splitlines():
        if marker in line:
            token = line.split()[-1]
            # handle formats with slash
            if "/" in token:
                token = token.split("/", 1)[0]
            token = token.rstrip("%")
            try:
                return float(token)
            except ValueError:
                return 0.0
    return 0.0

def main(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"Error: file not found: {pdf_path}")
        sys.exit(1)

    print(f"\n📄 Scoring resume: {pdf_path}\n")

    # 1) Structure (50%)
    ok, struct_out = safe_run([PY, "CV_scoring_structure.py", pdf_path])
    if ok:
        print("🧱 Structure:\n" + struct_out)
        struct_pct = extract_pct(struct_out, "Structure Score")
    else:
        print("🔴 Structure step failed:\n", struct_out)
        struct_pct = 0.0

    # 2) Text Preparation
    txt = "resume.txt"
    ok, prep_out = safe_run([PY, "data_preparation_CV.py", pdf_path, txt])
    if not ok:
        print("🔴 Text-prep failed, skipping Language & Presentation:\n", prep_out)
        lang_pct = pres_pct = 0.0
    else:
        # 3) Language Quality (40%)
        ok, lang_out = safe_run([PY, "CV_Language_score.py", txt])
        if ok:
            print("\n🗣 Language:\n" + lang_out)
            lang_pct = extract_pct(lang_out, "Quality Score")
        else:
            print("🔴 Language step failed:\n", lang_out)
            lang_pct = 0.0

        # 4) Presentation Quality (10%)
        ok, pres_out = safe_run([PY, "CV_presentation_scoring.py", pdf_path])
        if ok:
            print("\n🎨 Presentation:\n" + pres_out)
            pres_pct = extract_pct(pres_out, "Presentation Score")
        else:
            print("🔴 Presentation step failed:\n", pres_out)
            pres_pct = 0.0

    # 5) Aggregate weighted score
    print(f"\n▶️ Components: Structure={struct_pct}%, Language={lang_pct}%, Presentation={pres_pct}%")
    overall = round(
        struct_pct * 0.5 +
        lang_pct   * 0.4 +
        pres_pct   * 0.1,
        1
    )
    print(f"\n🏆 Overall CV Quality Score: {overall}/100\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python CV_score_quality.py path/to/resume.pdf")
        sys.exit(1)
    main(sys.argv[1])
