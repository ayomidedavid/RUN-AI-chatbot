# backend/load_courses.py
"""Load course_data.csv into a SQLite database.

The script performs the following steps:
1. Connects (or creates) a SQLite database file `course_data.db` in the backend folder.
2. Drops the existing `courses` table if it exists – this clears the earlier data.
3. Creates a fresh `courses` table with appropriate columns.
4. Reads `course_data.csv` and inserts every row into the table.
5. Commits the transaction and closes the connection.

Run the script with:
    python -m backend.load_courses
"""

import csv
import pathlib
import sqlite3
import re
from typing import List

DB_PATH = pathlib.Path(__file__).with_name("course_data.db")
CSV_PATH = pathlib.Path(__file__).with_name("course_data.csv")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL,
    course_title TEXT NOT NULL,
    units INTEGER NOT NULL,
    status TEXT NOT NULL,
    department TEXT,
    level INTEGER,
    semester TEXT
);
"""

INSERT_SQL = """
INSERT INTO courses (
    course_code, course_title, units, status, department, level, semester
) VALUES (?, ?, ?, ?, ?, ?, ?);
"""


def clear_and_create_table(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS courses;")
    cur.execute(CREATE_TABLE_SQL)
    conn.commit()


def load_csv_into_db(conn: sqlite3.Connection, csv_path: pathlib.Path) -> None:
    cur = conn.cursor()
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows: List[tuple] = []
        for row in reader:
            # Convert numeric fields
            units = int(row["Units"]) if row["Units"].isdigit() else 0
            level = int(row["Level"]) if row["Level"].isdigit() else None
            
            raw_code = row["Course Code"].strip()
            match = re.search(r'([A-Za-z]{3,4})\s*(\d{3})', raw_code)
            if match:
                normalized_code = f"{match.group(1).upper()} {match.group(2)}"
            else:
                normalized_code = raw_code
                
            rows.append(
                (
                    normalized_code,
                    row["Course Title"].strip(),
                    units,
                    row["Status"].strip(),
                    row["Department"].strip(),
                    level,
                    row["Semester"].strip(),
                )
            )
        cur.executemany(INSERT_SQL, rows)
    conn.commit()


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    clear_and_create_table(conn)
    load_csv_into_db(conn, CSV_PATH)
    conn.close()
    print(f"Database populated at {DB_PATH}")


if __name__ == "__main__":
    main()
