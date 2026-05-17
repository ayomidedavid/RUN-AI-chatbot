# backend/handbook_extractor.py
"""
Handbook Extractor
===================

This module parses the raw handbook text (``backend/extracted_data.txt``) and extracts
structured information for a number of frequently‑asked‑question topics.

The extracted data is written to CSV files in the same directory:
    grading_data.csv
    exam_rules.csv
    conduct_data.csv
    curriculum_data.csv
    staff_data.csv
    facilities_data.csv
    policies_data.csv

Each CSV uses a simple two‑column layout (Category, Detail) except where a more
structured table is appropriate (e.g., grade‑point mapping).  The extractor is
intended to be run as a script::

    python -m backend.handbook_extractor

The code is deliberately defensive – it tolerates extra whitespace, page‑break
artifacts and variations in heading formatting.
"""

import csv
import re
from pathlib import Path
from typing import Dict, List

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

HANDBOOK_PATH = Path(__file__).parent / "extracted_data.txt"
OUTPUT_DIR = Path(__file__).parent

def load_handbook() -> str:
    """Read the raw handbook text using UTF‑8 encoding."""
    return HANDBOOK_PATH.read_text(encoding="utf-8")

def split_into_sections(text: str) -> Dict[str, str]:
    """Return a mapping from *section title* to the block of text belonging to it.

    The handbook uses a numeric prefix (e.g. ``6. Grading System & CGPA``).
    We capture everything from a heading up to the next heading that starts
    with a number followed by a dot.
    """
    pattern = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+([A-Za-z0-9 &]+)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    sections: Dict[str, str] = {}
    for idx, match in enumerate(matches):
        title = match.group(2).strip()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        sections[title] = text[start:end].strip()
    return sections

def write_csv(filename: Path, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    """Write *rows* to *filename* using ``csv.DictWriter``."""
    with filename.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

# ---------------------------------------------------------------------------
# Section‑specific extractors
# ---------------------------------------------------------------------------

def extract_grading(block: str) -> List[Dict[str, str]]:
    """Parse the *Grading System & CGPA* block.

    Returns rows with ``Category`` and ``Detail``.  Where a clear table is
    present (e.g. ``A – 5.0``) we emit separate rows for each grade point.
    """
    rows: List[Dict[str, str]] = []
    # Normalise whitespace for easier regex matching
    clean = "\n".join(line.strip() for line in block.splitlines() if line.strip())

    # 1. Grade scale (A‑F) – look for a line that lists the letters
    scale_match = re.search(r"Grade\s*scale\s*[:‑]?\s*([A‑F ,]+)", clean, re.I)
    if scale_match:
        rows.append({"Category": "Grade Scale", "Detail": scale_match.group(1).replace(" ", "").strip()})

    # 2. Grade points – capture lines like "A – 5.0" or "A 5.0"
    grade_points: List[Dict[str, str]] = []
    for line in clean.splitlines():
        gp_match = re.match(r"^([A-F])\s*[\-–]?\s*([0-9]+(?:\.[0-9])?)", line)
        if gp_match:
            grade_points.append({"Letter": gp_match.group(1), "Point": gp_match.group(2)})
    if grade_points:
        # Export as a compact CSV representation within the two‑column file
        detail = ", ".join(f"{g['Letter']}:{g['Point']}" for g in grade_points)
        rows.append({"Category": "Grade Points", "Detail": detail})

    # 3. CGPA formula – look for a sentence containing "CGPA" and "formula"
    formula_match = re.search(r"CGPA\s*formula\s*[:‑]?\s*(.+)", clean, re.I)
    if formula_match:
        rows.append({"Category": "CGPA Formula", "Detail": formula_match.group(1).strip()})
    else:
        # fallback: any line that contains "CGPA" and an arithmetic expression
        fallback = next((ln for ln in clean.splitlines() if "CGPA" in ln and ("/" in ln or "*" in ln)), None)
        if fallback:
            rows.append({"Category": "CGPA Formula", "Detail": fallback.strip()})

    # 4. Degree classification – common phrasing e.g. "First Class", "Second Class"
    classification_matches = re.findall(r"(First Class|Second Class Upper|Second Class Lower|Third Class|Pass)\s*(?:\(.*?\))?", clean, re.I)
    if classification_matches:
        rows.append({"Category": "Degree Classification", "Detail": ", ".join(set(m.title() for m in classification_matches))})

    return rows


def extract_exam_rules(block: str) -> List[Dict[str, str]]:
    """Extract exam requirements, conduct rules, offences and penalties."""
    rows: List[Dict[str, str]] = []
    clean = "\n".join(line.strip() for line in block.splitlines() if line.strip())

    # Simple heuristics – look for bullet‑style lines starting with keywords
    for line in clean.splitlines():
        if re.search(r"attendance|ID card", line, re.I):
            rows.append({"Category": "Exam Requirement", "Detail": line})
        elif re.search(r"conduct|behaviour|behave", line, re.I):
            rows.append({"Category": "Exam Conduct", "Detail": line})
        elif re.search(r"impersonation|cheating|offence|plagiarism", line, re.I):
            rows.append({"Category": "Exam Offence", "Detail": line})
        elif re.search(r"rustication|expulsion|penalty", line, re.I):
            rows.append({"Category": "Penalty", "Detail": line})
    return rows


def extract_conduct(block: str) -> List[Dict[str, str]]:
    """Extract dress code, hostel rules, prohibited activities, library rules/fines."""
    rows: List[Dict[str, str]] = []
    clean = "\n".join(line.strip() for line in block.splitlines() if line.strip())
    for line in clean.splitlines():
        if re.search(r"dress code|attire", line, re.I):
            rows.append({"Category": "Dress Code", "Detail": line})
        elif re.search(r"hostel|dormitory", line, re.I):
            rows.append({"Category": "Hostel Rule", "Detail": line})
        elif re.search(r"prohibited|forbidden|not allowed", line, re.I):
            rows.append({"Category": "Prohibited Activity", "Detail": line})
        elif re.search(r"library|fine|overdue", line, re.I):
            rows.append({"Category": "Library Rule/Fine", "Detail": line})
    return rows


def extract_curriculum(block: str) -> List[Dict[str, str]]:
    """Extract courses per level, semester breakdown and total units.

    The existing ``course_data.csv`` already contains a flat list of courses.
    Here we provide a summary view extracted directly from the handbook.
    """
    rows: List[Dict[str, str]] = []
    clean = "\n".join(line.strip() for line in block.splitlines() if line.strip())
    # Detect level headings like "100 LEVEL" or "SECOND YEAR"
    level_pat = re.compile(r"(\d{3})\s+LEVEL", re.I)
    for line in clean.splitlines():
        lvl_match = level_pat.search(line)
        if lvl_match:
            rows.append({"Category": "Level", "Detail": lvl_match.group(1) + " Level"})
        # Detect total unit lines – often phrased as "Total Units: 120"
        unit_match = re.search(r"Total\s*Units\s*[:‑]?\s*(\d+)", line, re.I)
        if unit_match:
            rows.append({"Category": "Total Units", "Detail": unit_match.group(1)})
    return rows


def extract_staff(block: str) -> List[Dict[str, str]]:
    """Extract lecturer names, specialisations and positions.

    The function is tolerant of lines like:
        "1. Prof. J.O.A. Ayeni – Research TechniquesProfessor"
    It returns a compact representation (Name | Position).
    """
    rows: List[Dict[str, str]] = []
    clean = "\n".join(line.strip() for line in block.splitlines() if line.strip())
    entry_pat = re.compile(r"^\d+\.\s*([^–\-]+)[–\-]\s*(.+)$")
    for line in clean.splitlines():
        m = entry_pat.match(line)
        if m:
            name = m.group(1).strip()
            position = m.group(2).strip()
            rows.append({"Category": "Lecturer", "Detail": f"{name} – {position}"})
    return rows


def extract_facilities(block: str) -> List[Dict[str, str]]:
    """Extract labs, equipment and research facilities."""
    rows: List[Dict[str, str]] = []
    clean = "\n".join(line.strip() for line in block.splitlines() if line.strip())
    for line in clean.splitlines():
        if re.search(r"lab|laboratory|software|hardware|equipment", line, re.I):
            rows.append({"Category": "Facility", "Detail": line})
    return rows


def extract_policies(block: str) -> List[Dict[str, str]]:
    """Extract course registration rules, late‑registration penalties and add/drop deadlines."""
    rows: List[Dict[str, str]] = []
    clean = "\n".join(line.strip() for line in block.splitlines() if line.strip())
    for line in clean.splitlines():
        if re.search(r"registration|add/drop|deadline", line, re.I):
            rows.append({"Category": "Registration Policy", "Detail": line})
        if re.search(r"late.*registration|penalty", line, re.I):
            rows.append({"Category": "Late Registration Penalty", "Detail": line})
    return rows

# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def main() -> None:
    text = load_handbook()
    sections = split_into_sections(text)

    # Mapping of section titles to extractor functions and output filenames
    extraction_map = [
        ("Grading", extract_grading, OUTPUT_DIR / "grading_data.csv"),
        ("Examination", extract_exam_rules, OUTPUT_DIR / "exam_rules.csv"),
        ("Conduct", extract_conduct, OUTPUT_DIR / "conduct_data.csv"),
        ("Curriculum", extract_curriculum, OUTPUT_DIR / "curriculum_data.csv"),
        ("Programme Structure", extract_curriculum, OUTPUT_DIR / "curriculum_data.csv"),
        ("Staff", extract_staff, OUTPUT_DIR / "staff_data.csv"),
        ("Facilities", extract_facilities, OUTPUT_DIR / "facilities_data.csv"),
        ("Policies", extract_policies, OUTPUT_DIR / "policies_data.csv"),
    ]

    for title, func, out_path in extraction_map:
        # Try to find a matching section (case‑insensitive, allow extra words)
        block = ""
        for sec_title, sec_block in sections.items():
            if title.lower() in sec_title.lower():
                block = sec_block
                break
        # If still empty, fall back to the whole document
        if not block:
            block = text
        rows = func(block)
        if rows:
            write_csv(out_path, rows, ["Category", "Detail"])
            print(f"[+] {title}: {len(rows)} rows written to {out_path.name}")
        else:
            print(f"[!] {title}: no data extracted.")

if __name__ == "__main__":
    main()
