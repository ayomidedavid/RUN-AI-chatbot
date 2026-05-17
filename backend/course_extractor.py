# Course Table Extractor
"""
Parses the academic handbook text (`extracted_data.txt` by default) to extract every
course table (Course Code, Course Title, Units, Status) and writes a CSV file
with additional columns:
    - Department (derived from three‑letter prefix of the course code)
    - Level (numeric level, e.g., 100, 200)
    - Semester (FIRST or SECOND)

The output CSV (`backend/course_data.csv`) is ready for bulk import into a
database.
"""

import csv
import re
from pathlib import Path
from typing import List, Dict

# --------------------------------------------------------------------
# Configuration – adjust if needed
SOURCE_FILE = Path(__file__).parent / "extracted_data.txt"  # default source
OUTPUT_CSV = Path(__file__).parent / "course_data.csv"
# --------------------------------------------------------------------

# Regex patterns
TABLE_HEADER_RE = re.compile(
    r"(?P<semester>FIRST|SECOND)\s+SEMESTER\s+(?P<level>\d{3})\s+LEVEL",
    re.IGNORECASE,
)
COURSE_ROW_RE = re.compile(
    r"(?P<code>[A-Z]{3,4}\s?\d{3})\t(?P<title>.+?)\t(?P<units>\d+)\t(?P<status>[A-Z])"
)

# Simple department map – extend as needed
DEPT_MAP = {
    "CSC": "Computer Science",
    "GIT": "IT General",
    "GST": "General Studies",
    "MAT": "Mathematics",
    "PHY": "Physics",
    "BIO": "Biology",
    "CHE": "Chemistry",
    "CYB": "Cyber Security",
    "SEN": "Software Engineering",
    "IFT": "Information Technology",
    "INS": "Information Systems",
    # fallback handled below
}


def determine_department(course_code: str) -> str:
    """Map three‑letter prefix to a readable department name.

    If the prefix is unknown, returns "Other".
    """
    prefix = course_code.split()[0][:3]
    return DEPT_MAP.get(prefix, "Other")


def parse_file(text: str) -> List[Dict[str, str]]:
    """Extract rows from all course tables in the given text.

    Returns a list of dictionaries ready to be written to CSV.
    """
    rows: List[Dict[str, str]] = []
    current_semester = current_level = ""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Detect semester/level heading
        head_match = TABLE_HEADER_RE.search(line)
        if head_match:
            current_semester = head_match.group("semester").upper()
            current_level = head_match.group("level")
            i += 1
            continue
        # Detect start of a table
        if line.startswith("Course Code") and "Course Title" in line:
            # Skip header line
            i += 1
            while i < len(lines) and lines[i].strip():
                row_match = COURSE_ROW_RE.match(lines[i].strip())
                if not row_match:
                    break
                code = row_match.group("code").strip()
                rows.append({
                    "Course Code": code,
                    "Course Title": row_match.group("title").strip(),
                    "Units": row_match.group("units"),
                    "Status": row_match.group("status"),
                    "Department": determine_department(code),
                    "Level": current_level,
                    "Semester": current_semester,
                })
                i += 1
            continue
        i += 1
    return rows


def write_csv(rows: List[Dict[str, str]], out_path: Path) -> None:
    """Write extracted rows to a CSV file with a fixed column order."""
    fieldnames = [
        "Course Code",
        "Course Title",
        "Units",
        "Status",
        "Department",
        "Level",
        "Semester",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if not SOURCE_FILE.is_file():
        raise FileNotFoundError(f"Source file not found: {SOURCE_FILE}")
    text = SOURCE_FILE.read_text(encoding="utf-8")
    rows = parse_file(text)
    write_csv(rows, OUTPUT_CSV)
    print(f"Extracted {len(rows)} course rows → {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
