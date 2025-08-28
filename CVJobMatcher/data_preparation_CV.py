# data_preparation.py

#!/usr/bin/env python3
"""
Extracts and normalizes text from a CV PDF and writes it to a .txt file.

Usage:
    python data_preparation.py path/to/resume.pdf path/to/output.txt
"""
import re
import sys
import pdfplumber

def extract_text(pdf_path: str) -> str:
    """Extracts full text from the given PDF using pdfplumber."""
    full = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            full.append(txt)
    return "\n".join(full)

#def normalize_text(text: str) -> str:
   # """Lowercases, collapses whitespace, and strips."""
    #text = text.lower()
    #text = re.sub(r"\s+", " ", text)
    #return text.strip()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python data_preparation.py path/to/resume.pdf path/to/output.txt")
        sys.exit(1)

    pdf_path, out_txt = sys.argv[1], sys.argv[2]
    raw = extract_text(pdf_path)
    #norm = normalize_text(raw)

    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(raw)

    print(f"Extracted text written to {out_txt}")
