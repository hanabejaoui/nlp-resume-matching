
#!/usr/bin/env python3
import nltk
# Ensure stopwords are available for PyResParser
nltk.download('stopwords', quiet=True)
import sys
import re
from pyresparser import ResumeParser


# Define essential sections and map to ResumeParser keys
EXPECTED_SECTIONS = {
    "email": ["email"],
    "education": ["degree"],
    "experience": ["experience"],
    "skills": ["skills"]

}

def check_structure(pdf_path: str):
    """
    Checks if the resume at pdf_path contains all essential sections,
    prints missing/present list, section contents, and overall score.
    """
    # Extract with PyResParser
    data = ResumeParser(pdf_path).get_extracted_data()



    present = []
    missing = []
    section_contents = {}

    # For each expected section, look up any of its keys in data
    for label, keys in EXPECTED_SECTIONS.items():
        content = None
        for key in keys:
            # try both lowercase and uppercase keys
            if data.get(key) is not None:
                content = data.get(key)
                break
            if data.get(key.lower()) is not None:
                content = data.get(key.lower())
                break
        section_contents[label] = content
        if content:
            present.append(label)
        else:
            missing.append(label)

    # Report missing or all-present sections
    if missing:
        print(" Missing essential sections:")
        for sec in missing:
            print(f" - {sec}")
    else:
        print("All essential sections are present.")
    print()

    # Summary count & score
    total = len(EXPECTED_SECTIONS)
    count = len(present)
    score = round(count / total * 100, 1)
    print(f"Present sections ({count}/{total}): {', '.join(present)}")
    print(f"Structure Score: {count}/{total} -> {score}%\n")

    # Dump each section’s content
    print("Section Contents")
    for label in EXPECTED_SECTIONS:
        print(f"{label}:")
        print(section_contents[label])
        print()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python CV_scoring_structure.py path/to/your_resume.pdf")
        sys.exit(1)
    check_structure(sys.argv[1])
