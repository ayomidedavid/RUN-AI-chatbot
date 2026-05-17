import re
import os
import sys
from sqlalchemy.orm import Session

backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)
try:
    from backend.database import SessionLocal, engine, Base
    from backend.models import Course, Elective, PrerequisiteRule, FAQ, CareerMapping
except ImportError:
    sys.path.insert(0, backend_dir)
    from database import SessionLocal, engine, Base
    from models import Course, Elective, PrerequisiteRule, FAQ, CareerMapping

# Ensure tables exist
Base.metadata.drop_all(bind=engine)  # Clear existing tables
Base.metadata.create_all(bind=engine)  # Recreate tables

def parse_and_populate(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by START OF/END OF markers to ignore metadata, or just process the whole thing
    # Actually, the file has many sections. Let's process line by line or by blocks.
    
    # Regex to find course headers: CODE CODE-TITLE (UNITS, STATUS)
    # Example: CSC 475 — AUTOMATA THEORY (2 UNITS, COMPULSORY)
    # Example: CSC477-COMPUTER GRAPHICS (2 UNITS, ELECTIVE)
    # Handling OCR quirks like CsC, ELECT! IVE, symbols etc.
    course_pattern = re.compile(
        r'([A-Z]{3})\s*(\d{3})[:\s\-~]*([^(\n]*)(?:\((\d+)\s*[Uu][Nn][Ii][Tt][Ss]?,?\s*([A-Z! ]+)?\))?',
        re.IGNORECASE
    )

    db = SessionLocal()
    
    courses_added = 0
    electives_added = 0
    prereqs_added = 0

    # We'll split the text into chunks roughly by course code to handle descriptions
    # Find all matches for course headers
    matches = list(course_pattern.finditer(content))
    
    processed_codes = set()
    for i, match in enumerate(matches):
        prefix = match.group(1).upper()
        code_num = match.group(2)
        course_code = f"{prefix}{code_num}"
        
        # Skip if we already processed this code in this run to avoid duplicates before commit
        if course_code in processed_codes:
            continue
        processed_codes.add(course_code)
        
        title = match.group(3).strip().strip('—').strip('-').strip(':').strip()
        
        # Clean title from common OCR garbage
        title = re.sub(r'[^a-zA-Z0-9\s]', '', title).strip()
        
        raw_units = match.group(4)
        credits = int(raw_units) if raw_units and raw_units.isdigit() else 2
        
        raw_status = match.group(5)
        is_elective = False
        if raw_status:
            status_clean = raw_status.upper().replace('!', 'I').strip()
            if "ELECTIVE" in status_clean:
                is_elective = True

        # Get description: text between this match and next match
        start_pos = match.end()
        end_pos = matches[i+1].start() if i + 1 < len(matches) else len(content)
        description_block = content[start_pos:end_pos].strip()
        
        # Clean description
        description = " ".join(description_block.split())
        
        # Look for prerequisites in description
        prereq_match = re.search(r'PRE-?\s*REQUISITE[:\s]*([A-Z]{3})\s*(\d{3})', description, re.IGNORECASE)
        found_prereq = None
        if prereq_match:
            found_prereq = f"{prereq_match.group(1).upper()}{prereq_match.group(2)}"

        # 1. Upsert into Courses
        existing_course = db.query(Course).filter(Course.course_code == course_code).first()
        if not existing_course:
            new_course = Course(
                course_code=course_code,
                title=title if title else "Unknown Title",
                description=description[:1000] if description else "No description available.",
                credits=credits
            )
            db.add(new_course)
            db.flush() # Ensure it's tracked
            courses_added += 1
        else:
            # Update description if it was empty or shorter
            if description and (not existing_course.description or len(existing_course.description) < len(description)):
                existing_course.description = description[:1000]
                existing_course.title = title if title else existing_course.title
                existing_course.credits = credits

        # 2. Add to Electives if applicable
        if is_elective:
            existing_elective = db.query(Elective).filter(Elective.course_code == course_code).first()
            if not existing_elective:
                new_elective = Elective(
                    course_code=course_code,
                    title=title,
                    description=description[:500]
                )
                db.add(new_elective)
                electives_added += 1

    # Second pass for prerequisites to ensure all courses exist
    print("Processing prerequisites...")
    prereqs_to_add = []
    for i, match in enumerate(matches):
        prefix = match.group(1).upper()
        code_num = match.group(2)
        course_code = f"{prefix}{code_num}"
        
        # Look for prerequisites with more patterns
        # Looser regex to avoid header overlap issues
        prereq_matches = list(re.finditer(r'REQUISITE[:\s\-]*([A-Z]{2,4})[\s\-]*(\d{3})', description, re.IGNORECASE))
        if prereq_matches:
            print(f"Found {len(prereq_matches)} prereq matches for {course_code}")
        for pm in prereq_matches:
            found_prereq = f"{pm.group(1).upper()}{pm.group(2)}"
            print(f"  -> {found_prereq}")
            prereqs_to_add.append((course_code, found_prereq))

    for target, required in prereqs_to_add:
        # Just try to insert, ignoring duplicates for now via try/except
        try:
            new_rule = PrerequisiteRule(
                target_course_code=target.strip(),
                required_course_code=required.strip()
            )
            db.add(new_rule)
            db.commit()
            prereqs_added += 1
            print(f"  [SUCCESS] Added rule: {target} -> {required}")
        except Exception as e:
            db.rollback()
            # print(f"  [SKIP] Could not add rule {target}->{required}: {e}")
            pass

    # Add some initial Career Mappings if table is empty
    if db.query(CareerMapping).count() == 0:
        print("Adding seed Career Mappings...")
        careers = [
            ("Data Scientist", "CSC445"),
            ("Software Engineer", "CSC414"),
            ("Web Developer", "CSC312"),
            ("AI Specialist", "CSC409"),
            ("Database Administrator", "CSC343"),
            ("Mobile App Developer", "CSC411"),
            ("Cyber Security Analyst", "CYS201"),
            ("Network Administrator", "CSC321"),
            ("IT Consultant", "IFT101"),
            ("System Analyst", "CSC311"),
            ("Cloud Architect", "CSC432"),
            ("Machine Learning Engineer", "CSC445")
        ]
        for path, code in careers:
            db.add(CareerMapping(career_path=path, recommended_course_code=code))
    
    print("Checking seed FAQs...")
    faqs = [
        ("How do I register for courses?", "You can register through the student portal during the first two weeks of the semester."),
        ("What is a compulsory course?", "Compulsory courses are mandatory for your degree. You must pass them to graduate."),
        ("What are electives?", "Electives are optional courses you can choose based on your interest to complete your credit requirements."),
        ("How many units must I do before I graduate?", "To graduate, you generally must complete a minimum of 120 credit units for a standard 4-year degree programme (Direct Entry) or 160 units (100-level Entry), depending on your department."),
        ("What is the maximum workload?", "Students can register for a maximum of 25 units per semester, while the minimum is 15 units."),
        ("What is a carryover?", "A carryover occurs when you fail a compulsory course (score below 40%). You must retake and pass it in the next available semester."),
        ("What happens if my CGPA is below 1.0?", "You will be placed on academic probation. If it remains below 1.0 for two consecutive sessions, you may be asked to withdraw.")
    ]
    for q, a in faqs:
        if not db.query(FAQ).filter(FAQ.question == q).first():
            db.add(FAQ(question=q, answer=a))

    db.commit()
    db.close()
    
    print(f"Populating complete!")
    print(f"Courses added/updated: {courses_added}")
    print(f"Electives added: {electives_added}")
    print(f"Prerequisite rules added: {prereqs_added}")

if __name__ == "__main__":
    # Path relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(script_dir, "extracted_data.txt")
    parse_and_populate(data_file)

