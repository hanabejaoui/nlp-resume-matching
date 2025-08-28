# 🧰 CV Quality Analyzer & Job Matching

This project combines **CV Quality Analysis** and **Job ↔ CV Matching** into one pipeline.  
It allows you to evaluate the **quality of resumes** and **rank CVs against job postings** using NLP, TF–IDF, and cosine similarity.

---

## 📦 Repository Layout

STAGE/
│
├─ data_preparation_CV.py # Extracts text from CV PDFs (handles ligatures cleanup)
├─ matching.py # Match a CV (pdf/txt) to jobs in CSV (TF–IDF + cosine)
│
├─ CV_scoring_structure.py # Detects presence of sections (email, education, experience, skills)
├─ CV_Language_score.py # Counts errors, gives language quality score
├─ CV_presentation_scoring.py # Typography / layout / ATS checks
├─ CV_score_quality.py # Orchestrates the 3 scorers & aggregates the final score
│
├─ Sample_Job_Listings.csv # Example job dataset
├─ resume.txt # Example extracted CV text (generated)
│
├─ *.pdf # Example resumes (Hana, Nizar, etc.)
└─ Diagram.drawio # Architecture diagram


---

## ⚙️ Setup

```bash
# Create and activate a virtualenv
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

requirements.txt
pandas
numpy
scikit-learn
spacy==2.3.5
pdfplumber
pdfminer.six
nltk
yake

****How to Use
1) CV Quality Analysis
Run the end-to-end scorer:  
python CV_score_quality.py path/to/resume.pdf

It outputs:

Structure → Are email, education, experience, and skills sections present?

Language → Error rate, readability, language quality score

Presentation → Typography, layout, ATS compliance

Overall CV Quality Score

You can tune weights in CV_score_quality.py (e.g., Structure 50%, Language 40%, Presentation 10%).

2) Job Matching
Pass either a PDF (auto extraction) or pre-extracted TXT resume.

Pass either a PDF (auto extraction) or pre-extracted TXT resume.

It outputs:

Top K job matches (default = 5) from Sample_Job_Listings.csv

Each job’s requiredSkills

Skills detected in the CV and the overlap

Optional experience/seniority weighting


🧠 How Job Matching Works

Normalize & combine job title + description + requiredskills

TF–IDF vectorization of jobs + CV text

Cosine similarity to rank jobs

Skill overlap detection between job requirements and CV

Experience weighting (junior CVs vs senior roles)
