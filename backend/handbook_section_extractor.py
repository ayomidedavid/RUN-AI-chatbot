# backend/handbook_section_extractor.py
"""Extract selected handbook sections into CSV files.

The script looks for headings (case‑insensitive) that correspond to the
following areas and extracts the text until the next numbered heading or the end
of the document:
    • Examination Rules & Offences
    • Student Code of Conduct
    • Programme Structure (Curriculum)
    • Staff Information
    • Facilities & Resources
    • Policies & Procedures

Each extracted block is written to a CSV file (Category, Detail) in the same
folder.
"""

import csv
import re
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).parent
HANDBOOK_PATH = BASE_DIR / "extracted_data.txt"

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def load_handbook() -> str:
    """Read the raw handbook text using UTF‑8 encoding."""
    return HANDBOOK_PATH.read_text(encoding="utf-8")

def split_into_sections(text: str) -> Dict[str, str]:
    """Return a mapping of *section title* → *section body*.

    The handbook uses numbered headings like "6. Grading System & CGPA".
    We capture any line that starts with a number and a dot, store the title,
    and collect everything until the next such heading.
    """
    pattern = re.compile(r"^\d+\.\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    sections: Dict[str, str] = {}
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[title] = text[start:end].strip()
    return sections

def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    """Write rows to *path* using a two‑column layout (Category, Detail)."""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Category", "Detail"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

# ---------------------------------------------------------------------------
# Section‑specific extractors – very lightweight (just return the raw block).
# Each returns a list of rows where Category is the section name and Detail is the
# cleaned text block.
# ---------------------------------------------------------------------------

def make_rows(section_name: str, block: str) -> List[Dict[str, str]]:
    clean = "\n".join(l.strip() for l in block.splitlines() if l.strip())
    return [{"Category": section_name, "Detail": clean}] if clean else []

# Mapping of *search keywords* → (output CSV name, friendly title)
TARGETS = [
    ("Examination Rules & Offences", "exam_rules.csv", "Examination Rules & Offences"),
    ("Student Code of Conduct", "conduct_data.csv", "Student Code of Conduct"),
    ("Programme Structure (Curriculum)", "curriculum_data.csv", "Programme Structure (Curriculum)"),
    ("Staff Information", "staff_data.csv", "Staff Information"),
    ("Facilities & Resources", "facilities_data.csv", "Facilities & Resources"),
    ("Policies & Procedures", "policies_data.csv", "Policies & Procedures"),
]

def main() -> None:
    text = load_handbook()
    sections = split_into_sections(text)

    for keyword, filename, title in TARGETS:
        # Find the first section whose title contains the keyword (case‑insensitive)
        match_key = next((k for k in sections if keyword.lower() in k.lower()), None)
        if not match_key:
            print(f"[!] {title}: section not found.")
            continue
        block = sections[match_key]
        rows = make_rows(title, block)
        if rows:
            out_path = BASE_DIR / filename
            write_csv(out_path, rows)
            print(f"[+] {title}: written {len(rows)} row(s) to {out_path.name}")
        else:
            print(f"[!] {title}: no content extracted.")

if __name__ == "__main__":
    main()
