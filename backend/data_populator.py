import csv
import os
import sys
import re
from pathlib import Path

backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)
try:
    from backend.database import SessionLocal, engine, Base
    from backend.models import Course, CareerMapping, FAQ
except ImportError:
    sys.path.insert(0, backend_dir)
    from database import SessionLocal, engine, Base
    from models import Course, CareerMapping, FAQ

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def parse_and_populate(csv_path):
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    db = SessionLocal()
    seen_codes = set()

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        courses_added = 0
        skipped = 0

        for row in reader:
            code_raw = row["Course Code"].strip()
            title = row["Course Title"].strip()
            units_str = row["Units"].strip()
            status = row["Status"].strip().upper()
            department = row["Department"].strip()
            level_str = row["Level"].strip()
            semester = row["Semester"].strip().upper()

            credits = int(units_str) if units_str.isdigit() else 2
            level = int(level_str) if level_str.isdigit() else None

            match = re.search(r'([A-Za-z]{3,4})\s*(\d{3})', code_raw)
            if match:
                code = f"{match.group(1).upper()} {match.group(2)}"
            else:
                code = code_raw

            if not code:
                skipped += 1
                continue

            code_normalized = code.upper().replace(" ", "")
            if code_normalized in seen_codes:
                skipped += 1
                continue
            seen_codes.add(code_normalized)

            course = Course(
                course_code=code,
                title=title,
                description=f"{title} ({credits} units, {status}, {department}, {semester})",
                credits=credits,
                department=department,
                level=level,
                semester=semester,
                status=status,
            )
            db.add(course)
            courses_added += 1

    if db.query(CareerMapping).count() == 0:
        careers = [
            ("Data Scientist", "CSC445"),
            ("Software Engineer", "CSC414"),
            ("Web Developer", "CSC312"),
            ("AI Specialist", "CSC445"),
            ("Database Administrator", "CSC343"),
            ("Mobile App Developer", "CSC411"),
            ("Cyber Security Analyst", "CYB403"),
            ("Network Administrator", "CSC321"),
            ("IT Consultant", "IFT101"),
            ("System Analyst", "CSC311"),
            ("Cloud Architect", "CSC432"),
            ("Machine Learning Engineer", "CSC445"),
        ]
        for path, code in careers:
            db.add(CareerMapping(career_path=path, recommended_course_code=code))

    faqs = [
        ("How do I register for courses?", "You can register through the student portal during the first two weeks of the semester."),
        ("What is a compulsory course?", "Compulsory courses are mandatory for your degree. You must pass them to graduate."),
        ("What are electives?", "Electives are optional courses you can choose based on your interest to complete your credit requirements."),
        ("How many units must I do before I graduate?", "To graduate, you generally must complete a minimum of 120 credit units for Direct Entry or 160 units for 100-level Entry, depending on your department."),
        ("What is the maximum workload?", "Students can register for a maximum of 25 units per semester, while the minimum is 15 units."),
        ("What is a carryover?", "A carryover occurs when you fail a compulsory course (score below 40%). You must retake and pass it in the next available semester."),
        ("What happens if my CGPA is below 1.0?", "You will be placed on academic probation. If it remains below 1.0 for two consecutive sessions, you may be asked to withdraw."),
        ("How do I calculate my GPA?", "GPA = Sum of (Credit Units × Grade Points) / Sum of Credit Units. Grade points: A(70-100)=5, B(60-69)=4, C(50-59)=3, D(45-49)=2, E(40-44)=1, F(0-39)=0."),
    ]
    for q, a in faqs:
        if not db.query(FAQ).filter(FAQ.question == q).first():
            db.add(FAQ(question=q, answer=a))

    db.commit()
    db.close()

    print(f"Populating complete!")
    print(f"Courses added: {courses_added}")
    print(f"Duplicates skipped: {skipped}")

if __name__ == "__main__":
    csv_file = os.path.join(backend_dir, "course_data.csv")
    parse_and_populate(csv_file)
