import os
import sys

try:
    from backend.database import SessionLocal
    from backend.models import FAQ, CareerMapping
except ImportError:
    # Allow direct execution from the backend directory
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from database import SessionLocal
    from models import FAQ, CareerMapping

db = SessionLocal()

# Add more FAQs to cover the questions in question.txt
faqs_to_add = [
    ("What is the maximum unit I can register this semester?", "The maximum number of units you can register per semester is typically 24 units, but this may vary by department. Please check with your academic advisor."),
    ("What is the total number of units I should have registered and passed to graduate?", "To graduate, you typically need 120 credit units for a standard 4-year degree programme."),
    ("What is the total number of units I should have registered and passed as a direct entry student to graduate?", "As a direct entry student, you typically need 90-120 credit units depending on your programme."),
    ("I am not very good at programming, what elective should I register as a 200 level cybersecurity?", "For 200 level cybersecurity students who struggle with programming, we recommend starting with CSC275 (Introduction to Cybersecurity) which has less programming focus, or CSC271 (Computer Organization)."),
    ("If I score a total of 40 marks in test and exams, what grade would I have?", "With 40 marks, you would typically receive a D grade or pass mark. However, grading scales vary by department, so please check your course syllabus."),
    ("What is the minimum GPA I need to stay in the programme?", "The minimum GPA required is typically 2.0, but this may vary by department. Please check your student handbook."),
    ("What happens if my GPA falls below the required level?", "If your GPA falls below the minimum, you may be placed on academic probation and will need to improve your grades in subsequent semesters."),
    ("Can I add or drop a course after registration?", "Yes, you can add or drop courses during the add/drop period, usually within the first two weeks of the semester."),
    ("What should I do if there is a clash in my timetable?", "Consult with your academic advisor to find alternative courses or sections that don't conflict."),
    ("Can I retake a course I failed, and how does it affect my GPA?", "Yes, you can retake a failed course. The new grade will replace the failing grade in your GPA calculation."),
]

for question, answer in faqs_to_add:
    existing = db.query(FAQ).filter(FAQ.question == question).first()
    if not existing:
        db.add(FAQ(question=question, answer=answer))
        print(f"Added FAQ: {question[:50]}...")

# Add more career mappings
careers_to_add = [
    ("Cybersecurity", "CSC275"),
    ("Data Science", "CSC445"),
    ("Machine Learning", "CSC409"),
    ("Artificial Intelligence", "CSC409"),
    ("Cloud Computing", "CSC332"),
    ("DevOps", "CSC343"),
    ("Web Development", "CSC312"),
    ("Mobile Development", "CSC411"),
]

for career, code in careers_to_add:
    existing = db.query(CareerMapping).filter(CareerMapping.career_path == career).first()
    if not existing:
        db.add(CareerMapping(career_path=career, recommended_course_code=code))
        print(f"Added Career Mapping: {career} -> {code}")

db.commit()
print("Additional FAQs and Career Mappings added successfully!")
db.close()