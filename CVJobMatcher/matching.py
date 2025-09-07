#!/usr/bin/env python3
"""
job_cv_match.py

Purpose
-------
Match a single CV (PDF or TXT) to a list of job postings stored in a CSV,
using TF–IDF text features and cosine similarity.

How it works (high level)
-------------------------
1) Load jobs CSV and build a "combined" text per job: title + description + requiredskills.
2) Load the CV:
   - If it's a PDF, call `data_preparation_CV.py` to extract raw text.
   - If it's a TXT, read it directly.
3) Normalize all text (lowercase, strip punctuation, collapse spaces).
4) Fit a TF–IDF vectorizer on the union of job texts + the CV.
5) Compute cosine similarity between each job vector and the CV vector.
6) Print the top-K most similar jobs.

Usage
-----
  # Match a PDF CV (optionally supply K; default 5)
  python job_cv_match.py my_resume.pdf [k]

  # Or match a pre-extracted TXT
  python job_cv_match.py resume.txt [k]

Assumptions
-----------
- Jobs file is "Sample_Job_Listings.csv" in the current directory and has
  at least two columns: "title" and "description".
- `data_preparation_CV.py` lives in the same directory as this script and
  supports: python data_preparation_CV.py <pdf_path> <output_txt_path>
"""

import sys, re, os, tempfile, subprocess
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def normalize_text(text: str) -> str:
    """
    Lightweight normalization for English text:
      - lowercasing
      - remove non-alphanumeric characters (keep spaces)
      - collapse repeated whitespace

    This keeps the pipeline simple and fast; TF–IDF will handle tokenization
    and stopwords later.
    """
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_pdf_to_text(pdf_path: str) -> str:
    """
    Convert a PDF CV to raw text by delegating to `data_preparation_CV.py`.

    Why a subprocess?
      - Keeps PDF extraction logic isolated in one place.
      - Avoids importing heavy PDF libs here if you sometimes pass a TXT.

    Returns
      Raw (un-normalized) text extracted from the PDF.
    """
    # Resolve helper script next to this file
    script = os.path.join(os.path.dirname(__file__), "data_preparation_CV.py")

    # Use a real temp file so we can read what the helper wrote
    with tempfile.NamedTemporaryFile("r+", suffix=".txt", delete=False) as tmp:
        # Run: python data_preparation_CV.py <pdf> <tmp.txt>
        subprocess.run([sys.executable, script, pdf_path, tmp.name], check=True)
        # Rewind and read text out of the temp file
        tmp.seek(0)
        return tmp.read()


def main(argv):
    # Basic CLI: `python job_cv_match.py <cv_path> [k]`
    if not (2 <= len(argv) <= 3):
        print(__doc__)
        sys.exit(1)

    cv_input = argv[1]                 # path to CV .pdf or .txt
    k = int(argv[2]) if len(argv) == 3 else 5  # top-K matches to print

    # 1) Load jobs and build a combined text column (title + description)
    #    - Fill NaNs with "" to avoid TypeErrors when concatenating.
    jobs = pd.read_csv("Sample_Job_Listings.csv")
    jobs["combined"] = (
        jobs["title"].fillna("") + " " + jobs["description"].fillna("") + " " + jobs["requiredSkills"].fillna("")
    ).apply(normalize_text)

    # 2) Load the CV text based on its extension:
    #    - PDF: extract via helper
    #    - TXT: read directly
    if cv_input.lower().endswith(".pdf"):
        raw = extract_pdf_to_text(cv_input)
    else:
        raw = open(cv_input, encoding="utf-8", errors="ignore").read()
    cv_text = normalize_text(raw)

    # 3) Vectorize with TF–IDF
    #    Fit on union (all jobs + this CV) so the vocabulary covers both,
    #    then transform jobs and CV separately to get their vectors.
    corpus = pd.concat([jobs["combined"], pd.Series([cv_text])], ignore_index=True)
    vect = TfidfVectorizer(max_features=200, stop_words="english")
    vect.fit(corpus)
    job_mat = vect.transform(jobs["combined"])
    cv_mat  = vect.transform([cv_text])

    # 4) Cosine similarity: higher = more similar content
    sims = cosine_similarity(job_mat, cv_mat).flatten()

    # 5) Take top-K indices by similarity (descending)
    idxs = sims.argsort()[::-1][:k]

    # Pretty print the shortlist
    print(f"\nTop {k} matches for `{cv_input}`:\n")
    for rank, i in enumerate(idxs, 1):
        print(f"{rank}. [{i}] {jobs.at[i, 'title']!r} — score {sims[i]:.3f}")


if __name__ == "__main__":
    main(sys.argv)
