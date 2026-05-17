# backend/grading_extractor_simple.py
"""Simple grading extractor for Redeemer's University handbook.

Reads ``backend/extracted_data.txt`` and creates ``backend/grading_data.csv``
containing:
  - Grade Scale (letters)
  - Grade Points (letter -> point)
  - CGPA formula
  - Degree Classification list
"""

import csv
import re
from pathlib import Path

HANDBOOK = Path(__file__).parent / "extracted_data.txt"
OUTPUT = Path(__file__).parent / "grading_data.csv"

def load_text() -> str:
    return HANDBOOK.read_text(encoding="utf-8")

def extract_grade_scale(text: str):
    """Return a list of (letter, point) tuples.
    Looks for a markdown‑style table like:
        | Score (%) | Letter Grade | Grade Point (GP) |
        | 70 – 100  | A            | 5.00            |
    """
    rows = []
    # Find the header line to ensure we are in the right table
    table_start = re.search(r"Score\s*%?\s*\|\s*Letter\s*Grade\s*\|\s*Grade\s*Point", text, re.I)
    if not table_start:
        return rows
    # Extract lines after the header until a blank line or a non‑table line
    table_text = text[table_start.end():]
    for line in table_text.splitlines():
        line = line.strip()
        if not line or not line.startswith("|"):
            break
        # Remove leading/trailing '|'
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        # cells[0] = score range, cells[1] = letter, cells[2] = point
        letter = cells[1]
        point = cells[2]
        rows.append((letter, point))
    return rows

def extract_cgpa_formula(text: str):
    """Return the first line that looks like a CGPA formula."""
    # Look for a line containing 'CGPA' and an '=' sign
    for line in text.splitlines():
        if "CGPA" in line and "=" in line:
            # Clean spacing
            return line.strip()
    return None

def extract_degree_classifications(text: str):
    """Return a list of degree classification strings found in the text."""
    classifications = []
    patterns = [
        r"First Class",
        r"Second Class Upper",
        r"Second Class Lower",
        r"Third Class",
        r"Pass",
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, re.I):
            classifications.append(m.group(0).title())
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for c in classifications:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique

def main():
    text = load_text()
    rows: list[dict[str, str]] = []

    # Grade Scale (letters only)
    letters = [letter for letter, _ in extract_grade_scale(text)]
    if letters:
        rows.append({"Category": "Grade Scale", "Detail": ", ".join(letters)})

    # Grade Points
    gp = extract_grade_scale(text)
    if gp:
        detail = ", ".join(f"{l}:{p}" for l, p in gp)
        rows.append({"Category": "Grade Points", "Detail": detail})

    # CGPA Formula
    formula = extract_cgpa_formula(text)
    if formula:
        rows.append({"Category": "CGPA Formula", "Detail": formula})

    # Degree Classification
    classes = extract_degree_classifications(text)
    if classes:
        rows.append({"Category": "Degree Classification", "Detail": ", ".join(classes)})

    # Write CSV
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Category", "Detail"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"[+] grading_data.csv written with {len(rows)} rows")

if __name__ == "__main__":
    main()
