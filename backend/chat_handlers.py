import re
import difflib
import logging
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from .models import Course, CareerMapping, FAQ

logger = logging.getLogger(__name__)

DEPARTMENTS = {
    "Computer Science": ["CMP", "CSC", "COS"],
    "Cyber Security": ["CYB"],
    "Information Technology": ["IFT"],
    "Software Engineering": ["SEN"],
    "Information Systems": ["INS", "IFS"],
    "IT General": ["GIT"],
    "General Studies": ["GST"],
    "Mathematics": ["MAT", "MTH"],
    "Physics": ["PHY"],
    "Biology": ["BIO"],
    "Chemistry": ["CHE", "CHM"],
}

DEPARTMENT_KEYWORDS = {
    "computer science": "Computer Science",
    "csc": "Computer Science",
    "cyber security": "Cyber Security",
    "cyb": "Cyber Security",
    "cyber": "Cyber Security",
    "information technology": "Information Technology",
    "ift": "Information Technology",
    "it": "Information Technology",
    "software engineering": "Software Engineering",
    "sen": "Software Engineering",
    "information systems": "Information Systems",
    "ins": "Information Systems",
    "ifs": "Information Systems",
    "general studies": "General Studies",
    "gst": "General Studies",
    "mathematics": "Mathematics",
    "maths": "Mathematics",
    "mth": "Mathematics",
    "mat": "Mathematics",
    "physics": "Physics",
    "phy": "Physics",
    "biology": "Biology",
    "bio": "Biology",
    "chemistry": "Chemistry",
    "che": "Chemistry",
    "chm": "Chemistry",
}

def extract_course_code(text, db=None):
    match = re.search(r'([a-zA-Z]{3})\s*([0-9]{3})', text)
    if match:
        return f"{match.group(1).upper()} {match.group(2)}"
        
    if db:
        potential = re.findall(r'\b[a-zA-Z]{2,4}\s*[0-9]{2,3}\b', text)
        if potential:
            all_codes = [c.course_code for c in db.query(Course).all()]
            for p in potential:
                p_norm = p.upper().replace(" ", "")
                all_codes_no_space = {c.replace(" ", ""): c for c in all_codes}
                matches = difflib.get_close_matches(p_norm, all_codes_no_space.keys(), n=1, cutoff=0.7)
                if matches:
                    return all_codes_no_space[matches[0]]
    return None

def extract_department(text):
    text_lower = text.lower()
    for keyword, dept in DEPARTMENT_KEYWORDS.items():
        if keyword in text_lower:
            return dept
            
    words = text_lower.split()
    candidates = [" ".join(words[i:i+2]) for i in range(len(words)-1)] + words
    
    dept_names = list(DEPARTMENT_KEYWORDS.keys())
    for cand in candidates:
        if len(cand) > 3:
            matches = difflib.get_close_matches(cand, dept_names, n=1, cutoff=0.8)
            if matches:
                return DEPARTMENT_KEYWORDS[matches[0]]
                
    return None

def extract_level(text):
    match = re.search(r'(\d{3})\s*(?:level|l|lvl)\b', text.lower())
    if match:
        return int(match.group(1)[0]) * 100
    match = re.search(r'(first|second|third|fourth)\s*year', text.lower())
    if match:
        years = {"first": 100, "second": 200, "third": 300, "fourth": 400}
        return years.get(match.group(1), None)
    return None

def extract_semester(text):
    text_lower = text.lower()
    if re.search(r'\b(first|1st)\s*sem(?:ester)?\b|\bsemester\s*1\b', text_lower):
        return "FIRST"
    if re.search(r'\b(second|2nd)\s*sem(?:ester)?\b|\bsemester\s*2\b', text_lower):
        return "SECOND"
    return None

def handle_greeting(session_context):
    response_text = "Hello! I am ACADEMIC QUERY, your intelligent academic adviser. You can ask me about courses, electives, registration, graduation requirements, GPA, or career paths. How can I help you today?"
    if not session_context.get("department_confirmed"):
        response_text += " To provide the most accurate advice, could you please tell me your department? (Computer Science, Cyber Security, or Information Technology)"
    return response_text

def handle_small_talk(user_query, session_context):
    text = re.sub(r'[^a-z0-9\s]', '', user_query.lower()).strip()
    text = re.sub(r'\s+', ' ', text)

    if not text:
        return None

    greeting_phrases = {
        "hi", "hello", "hey", "heyy", "yo", "sup", "whats up", "good morning",
        "good afternoon", "good evening", "morning", "afternoon", "evening",
        "how far", "how body", "wetin dey", "bawo ni", "e kaaro", "e kaasan",
        "e kaale", "kedu", "ndewo", "sannu", "ina kwana", "ina wuni"
    }
    wellbeing_phrases = {
        "how are you", "how are you doing", "how you doing", "how is it going",
        "hows it going", "are you okay", "you good", "se daadaa ni",
        "kedu ka imere", "yaya dai", "ya kake", "ya kike"
    }
    thanks_phrases = {
        "thanks", "thank you", "thank u", "appreciate it", "nice one",
        "ese", "daalu", "nagode"
    }
    bye_phrases = {
        "bye", "goodbye", "see you", "see ya", "later", "talk later",
        "odabo", "ka odi", "sai anjima"
    }
    acknowledgement_phrases = {
        "ok", "okay", "alright", "cool", "nice", "great", "fine", "lol", "haha",
        "oya", "sharp", "no wahala", "wahala no dey"
    }

    if text in greeting_phrases:
        return "greeting", handle_greeting(session_context)

    if text in wellbeing_phrases:
        return ("small_talk",
            "I'm doing well, thanks for asking. I'm ready to help with courses, registration, GPA, graduation, or career advice.")

    if text in thanks_phrases:
        return "small_talk", "You're welcome. What else would you like to check?"

    if text in bye_phrases:
        return "small_talk", "Alright, talk to you later. Good luck with your academics."

    if text in acknowledgement_phrases:
        return "small_talk", "Got it. You can ask me another academic question whenever you're ready."

    if len(text.split()) <= 3 and any(word in text.split() for word in ["please", "help", "bro", "dear"]):
        return "small_talk", "I'm here. Ask me anything about your courses, registration, GPA, graduation, or career path."

    return None

def normalize_multilingual_query(user_query):
    text = user_query.lower()
    replacements = {
        "wetin be": "what is",
        "wetin is": "what is",
        "wetin": "what",
        "abeg": "",
        "i wan": "i want to",
        "i fit": "can i",
        "i go fit": "can i",
        "make i": "can i",
        "carry": "register",
        "take": "register",
        "course wey": "course that",
        "how many unit": "how many units",
        "melo ni": "how many",
        "kini": "what is",
        "kedu ihe bu": "what is",
        "gini bu": "what is",
        "menene": "what is",
        "nawa ne": "how many",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return re.sub(r'\s+', ' ', text).strip()

def handle_capabilities(session_context):
    return (
        "I can help you with a wide range of academic queries, including:\n"
        "- **Course Info**: Details about specific courses and their credit units.\n"
        "- **Electives**: Recommendations based on your level and career goals.\n"
        "- **Registration**: Guidance on unit limits, add/drop periods, and timetable clashes.\n"
        "- **Graduation**: Tracking your progress towards the 160 units (120 for Direct Entry) requirement.\n"
        "- **GPA**: Explaining the 5.0 scale and how to compute your GPA.\n"
        "- **Careers**: Mapping courses to paths like Data Science or Cybersecurity.\n\n"
        "What would you like to know more about?"
    )

def build_course_query(db, user_query, session_context):
    q = db.query(Course)
    filters = []

    query_dept = extract_department(user_query)
    dept = query_dept if query_dept else (session_context.get("department") if session_context.get("department_confirmed") else None)
    
    if dept:
        prefixes = DEPARTMENTS.get(dept, [])
        if prefixes:
            or_filters = [Course.course_code.like(f"{p}%") for p in prefixes]
            filters.append(or_(*or_filters))

    level = extract_level(user_query)
    if level:
        filters.append(Course.level == level)

    semester = extract_semester(user_query)
    if semester:
        filters.append(Course.semester == semester.upper())

    if filters:
        q = q.filter(and_(*filters) if len(filters) > 1 else filters[0])

    return q, dept

def handle_course_info(db, user_query, course_code, session_context):
    if course_code:
        normalized = course_code.replace(" ", "").upper()
        courses = db.query(Course).all()
        course = None
        for c in courses:
            if c.course_code.replace(" ", "").upper() == normalized:
                course = c
                break
        if course:
            dept_info = f" ({course.department})" if course.department else ""
            sem_info = f" - {course.semester} Semester" if course.semester else ""
            level_info = f" {course.level} Level" if course.level else ""
            status_info = " (Compulsory)" if course.status == "C" else " (Elective)" if course.status == "E" else ""
            return f"Here is the information for {course.title} ({course.course_code}){dept_info}{level_info}{sem_info}: {course.description}. Credits: {course.credits}{status_info}."
        return f"I'm sorry, I couldn't find any information on {course_code} in our database."

    level = extract_level(user_query)
    semester = extract_semester(user_query)
    
    q, effective_dept = build_course_query(db, user_query, session_context)
    courses = q.order_by(Course.level, Course.semester, Course.course_code).limit(15).all()

    if courses:
        dept_label = f" for {effective_dept}" if effective_dept else ""
        level_label = f" {level} Level" if level else ""
        sem_label = f" {semester} Semester" if semester else ""
        items = [f"{c.course_code}: {c.title} ({c.credits} units)" for c in courses]
        return f"Here are the courses{dept_label}{level_label}{sem_label}:\n- " + "\n- ".join(items)

    dept_prompt = "" if effective_dept else " Also, please tell me your department."
    return "It seems you're asking about course options. What level are you asking about (e.g., 200 level, 300 level)?" + dept_prompt

def handle_electives(db, user_query, session_context):
    if "career" in user_query and any(k in user_query for k in ["cybersecurity", "software engineering", "data science"]):
        return (
            "For career-focused electives, choose based on your target path:\n"
            "- Cybersecurity: prioritize security, networking, system security, and information defence courses.\n"
            "- Software Engineering: prioritize object-oriented programming, software engineering, databases, and web/mobile development courses.\n"
            "- Data Science: prioritize statistics, databases, data analysis, artificial intelligence, and machine learning related courses."
        )

    q = db.query(Course).filter(Course.status == "E")

    level = extract_level(user_query)
    if level:
        q = q.filter(Course.level == level)

    semester = extract_semester(user_query)
    if semester:
        q = q.filter(Course.semester == semester.upper())

    query_dept = extract_department(user_query)
    dept = query_dept if query_dept else (session_context.get("department") if session_context.get("department_confirmed") else None)
    if dept:
        prefixes = DEPARTMENTS.get(dept, [])
        if prefixes:
            or_filters = [Course.course_code.like(f"{p}%") for p in prefixes]
            q = q.filter(or_(*or_filters))

    electives = q.order_by(Course.level, Course.semester, Course.course_code).limit(10).all()
    if electives:
        items = [f"{e.course_code}: {e.title} ({e.credits} units)" for e in electives]
        return "Here are some electives you can take:\n- " + "\n- ".join(items)

    return "I couldn't find any electives matching that level/department. Try specifying a level (e.g., '300 level') or your department."

def handle_registration(db, user_query, session_context):
    level = extract_level(user_query)
    query_dept = extract_department(user_query)
    dept = query_dept if query_dept else (session_context.get("department") if session_context.get("department_confirmed") else None)
    semester = extract_semester(user_query)

    if "how many" in user_query or "maximum" in user_query or "unit" in user_query:
        if "direct entry" in user_query:
            return "As a direct entry or transfer student into 200 Level, you are allowed to request for a maximum of 3 extra units per semester (totaling up to 28 units), subject to Senate's approval. The standard maximum is 25 units."
        return "Every student is expected to register for a minimum of 15 credit units per semester and a maximum of 25 credit units."

    if "extra" in user_query or "beyond" in user_query:
        return "Yes, you can typically take extra courses beyond your required load (up to the 25-unit limit). If you are a direct entry student, you can request up to 3 extra units beyond the standard maximum with Senate approval."

    if "compulsory" in user_query or "required" in user_query or "should i register" in user_query:
        q = db.query(Course).filter(Course.status == "C")
        if level:
            q = q.filter(Course.level == level)
        if semester:
            q = q.filter(Course.semester == semester.upper())
        if dept:
            prefixes = DEPARTMENTS.get(dept, [])
            if prefixes:
                or_filters = [Course.course_code.like(f"{p}%") for p in prefixes]
                q = q.filter(or_(*or_filters))

        courses = q.order_by(Course.course_code).limit(15).all()
        if courses:
            items = [f"{c.course_code}: {c.title}" for c in courses]
            dept_label = f" for {dept}" if dept else ""
            level_label = f" {level} Level" if level else ""
            return f"Here are the compulsory courses{dept_label}{level_label}:\n- " + "\n- ".join(items)
        return "To see your compulsory courses, please specify your level (e.g., '200 level'). Compulsory courses are those you must pass to qualify for graduation."

    if "add" in user_query or "drop" in user_query:
        return "You can add or drop courses within two weeks after the close of the registration period. Deletion is only allowed up to three weeks before exams start."

    if "clash" in user_query or "timetable" in user_query:
        return "If there are omissions or clashes in your timetable, you must promptly draw the attention of your Head of Department for immediate action."

    return "For registration questions, you can ask about unit limits, compulsory courses for your level, or add/drop deadlines."

def handle_graduation(db, user_query):
    if "direct entry" in user_query:
        return "For entrants at the 200 Level (Direct Entry), a minimum of 120 units is required for graduation. You must also obtain units in all 100-level GST courses if you haven't taken them elsewhere."
    if "minimum" in user_query or "how many" in user_query or "total" in user_query:
        return "For entrants at the 100 Level, a minimum of 160 units is required for graduation. All units passed must include all compulsory courses."
    if "plan" in user_query or "on time" in user_query or "meeting" in user_query:
        return "To graduate on time, ensure you pass all compulsory courses at each level. You can track your progress by checking your CGPA and total units against the 160-unit requirement (120 for Direct Entry)."
    return "Graduation requirements include passing all compulsory courses and meeting the minimum unit requirement (160 for 100-level entry, 120 for 200-level entry)."

def calculate_gpa_from_text(text):
    matches1 = re.findall(r'(\d)\s*(?:units?|credits?|u|c)?\s*(?:-|:|,|=)?\s*([A-Fa-f])\b', text, re.IGNORECASE)
    matches2 = re.findall(r'\b([A-Fa-f])\s*(?:-|:|,|=)?\s*(\d)\s*(?:units?|credits?|u|c)?\b', text, re.IGNORECASE)
    
    matches = matches1 if len(matches1) >= len(matches2) else [(u, g) for g, u in matches2]
    
    if not matches:
        return None
        
    grade_points = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1, "F": 0}
    total_qp = 0
    total_units = 0
    
    breakdown = []
    for units_str, grade in matches:
        units = int(units_str)
        gp = grade_points.get(grade.upper())
        if gp is not None and units > 0:
            total_qp += units * gp
            total_units += units
            breakdown.append(f"{units} units of {grade.upper()}")
            
    if total_units > 0:
        gpa = total_qp / total_units
        return f"I calculated your GPA based on the grades provided:\n- Breakdown: {', '.join(breakdown)}\n- Total Units: {total_units}\n- Total Quality Points: {total_qp}\n\n**Your calculated GPA is: {gpa:.2f}**"
    return None

def handle_gpa(user_query):
    calc_result = calculate_gpa_from_text(user_query)
    if calc_result:
        return calc_result

    if "first class begins" in user_query or "class of degree" in user_query or "degree classification" in user_query:
        return (
            "Degree Classifications based on CGPA:\n"
            "- First Class Honours: 4.50 - 5.00\n"
            "- Second Class Honours (Upper Division): 3.50 - 4.49\n"
            "- Second Class Honours (Lower Division): 2.40 - 3.49\n"
            "- Third Class Honours: 1.50 - 2.39\n"
            "- Pass: 1.00 - 1.49\n"
            "- Fail: Below 1.00\n\n"
            "So, First Class begins from 4.50 CGPA."
        )
    if "calculate" in user_query or "calculated" in user_query or "how is" in user_query or "compute" in user_query:
        return (
            "I can help you calculate your CGPA right here! Just list your units and grades in your next message.\n\n"
            "For example, you can say: `I got 3 units A, 3 units B, and 2 units C` or just `3A, 3B, 2C`.\n\n"
            "Alternatively, if you're doing it manually, the formula is: Sum of (Credit Units x Grade Points) / Sum of (Credit Units).\n"
            "Grade Scale: A=5, B=4, C=3, D=2, E=1, F=0."
        )
    if "minimum" in user_query or "stay" in user_query or "below" in user_query:
        return "To stay in the program, you must maintain a minimum CGPA of 1.00. If your CGPA falls below 1.00 for two consecutive semesters, you will be placed on probation, and potentially asked to withdraw if it doesn't improve."
    if "retake" in user_query or "failed" in user_query:
        return "Yes, you can retake a course. If it is a compulsory course, you MUST retake and pass it. For CGPA calculation, all attempts are included, meaning the failed grade still counts towards your total units attempted."
    if "40 marks" in user_query or "score 40" in user_query:
        return "A total score of 40-44 marks corresponds to an 'E' grade, which carries 1 grade point on the 5.0 scale. It is considered a pass. Scores below 40 are 'F' (0 points)."
    return "The grading system is based on a 5.0 scale: A(70-100)=5, B(60-69)=4, C(50-59)=3, D(45-49)=2, E(40-44)=1, F(0-39)=0."

def handle_career(db, user_query):
    if "cybersecurity" in user_query:
        return "For a career in Cybersecurity, focus on courses like CYB 203 (Cyber Security in Business), CYB 309 (System Security), and Information Defence Technologies (IFT 254)."
    if "software engineering" in user_query:
        return "For Software Engineering, prioritize SEN 201 (Intro to Software Engineering), CSC 212 (Object-Oriented Programming), and Software Construction (SEN 206)."
    if "data science" in user_query or "data mining" in user_query:
        return "For Data Science, focus on IFT 301 (Data Analysis), CSC 343 (Database Systems), and Data Mining topics usually covered in advanced electives."
    if "not very good at programming" in user_query:
        return "If programming isn't your strength, you might consider electives like Management Information Systems (INS 207) or Information Technology in Business (IFT 205) which focus more on the application and management side."

    mappings = db.query(CareerMapping).all()
    for m in mappings:
        if m.career_path.lower() in user_query:
            return f"To pursue a career as a {m.career_path}, we recommend taking {m.recommended_course_code}."

    return "We have advice for various career paths. Tell me which field you're interested in, such as Cybersecurity, Data Science, or Web Development."

def handle_fallback(db, user_query):
    faqs = db.query(FAQ).all()
    faq_questions = [faq.question.lower() for faq in faqs]
    matches = difflib.get_close_matches(user_query, faq_questions, n=1, cutoff=0.5)
    if matches:
        matched_q = matches[0]
        matched_faq = next(f for f in faqs if f.question.lower() == matched_q)
        return matched_faq.answer, "faq"

    course_matches = db.query(Course).filter(
        (Course.title.ilike(f"%{user_query}%")) |
        (Course.description.ilike(f"%{user_query}%"))
    ).limit(3).all()

    if course_matches:
        items = [f"{c.course_code}: {c.title}" for c in course_matches]
        return f"I couldn't find an exact answer, but here are some related courses:\n- " + "\n- ".join(items), "course_search"

    return "", "fallback"

def handle_timetable(db, user_query, session_context):
    dept = session_context.get("department") or extract_department(user_query)
    level = extract_level(user_query)
    semester = extract_semester(user_query) or 1
    
    if not dept:
        profile = session_context.get("user_profile", {})
        dept = profile.get("department")
        level = level or profile.get("level")
        
    if not dept or not level:
        return "To generate a timetable, I need your department and level (e.g., 'Generate timetable for 300L Computer Science'). If you set your Profile in the sidebar, I'll know this automatically!"

    query = db.query(Course).filter(Course.department == dept, Course.level == level)
    if semester:
        query = query.filter(Course.semester == semester)
        
    compulsory_courses = query.filter(Course.is_compulsory == True).all()
    elective_courses = query.filter(Course.is_compulsory == False).limit(2).all()
    
    if not compulsory_courses:
        return f"I couldn't find any courses for {level}L {dept} in my database."
        
    lines = [f"Here is a recommended Semester Plan for {level}L {dept} (Semester {semester}):\n"]
    lines.append("| Course Code | Title | Units | Type |")
    lines.append("|---|---|---|---|")
    
    total_units = 0
    for c in compulsory_courses:
        lines.append(f"| **{c.course_code}** | {c.title} | {c.credits} | Compulsory |")
        total_units += c.credits
        
    for c in elective_courses:
        lines.append(f"| **{c.course_code}** | {c.title} | {c.credits} | Elective |")
        total_units += c.credits
        
    lines.append(f"\n**Total Expected Units:** {total_units}")
    return "\n".join(lines)
