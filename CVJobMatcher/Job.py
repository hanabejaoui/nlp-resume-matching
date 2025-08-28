import pandas as pd
import re
import ast
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter

# 1) Load data
df = pd.read_csv('Sample_Job_Listings.csv')

# 2) Normalize free-text fields & combine for TF–IDF
def normalize_text(text):
    text = (text or "").lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

df['combined_text'] = (
    df['title'].fillna('') + ' ' +
    df['description'].fillna('')
).apply(normalize_text)

print("Step 1: Combined & Normalized Text")
print(df[['combined_text']].head(), "\n")

# 3) TF–IDF Vectorization
vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
tfidf_matrix = vectorizer.fit_transform(df['combined_text'])

print("Step 2: TF–IDF")
print(" - Matrix shape:", tfidf_matrix.shape)
print(" - Sample features:", vectorizer.get_feature_names_out()[:10], "\n")

# 4) Robust parsing of `requiredSkills` column
def parse_skills(cell):
    if pd.isna(cell) or not cell.strip():
        return []
    cell = cell.strip()
    # Try Python list literal first:
    if cell.startswith('[') and cell.endswith(']'):
        try:
            lst = ast.literal_eval(cell)
            return [str(s).strip().lower() for s in lst]
        except (ValueError, SyntaxError):
            pass
    # Fallback: semicolon or comma separation
    parts = re.split(r'[;,]', cell)
    return [p.strip().lower() for p in parts if p.strip()]

df['skills_list'] = df['requiredSkills'].apply(parse_skills)

# 5) Top-20 most frequent skills
all_skills = [skill for sub in df['skills_list'] for skill in sub]
top20 = [skill for skill, _ in Counter(all_skills).most_common(20)]

print("Step 3: Top-20 Skills")
print(top20, "\n")

# 6) One-hot encode those top-20
for skill in top20:
    df[f'skill_{skill}'] = df['skills_list'].apply(lambda lst: int(skill in lst))

print("One-hot encoded skills (first 5 rows):")
print(df[[f'skill_{s}' for s in top20]].head())
