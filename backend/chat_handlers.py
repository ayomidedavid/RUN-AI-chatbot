import re
import difflib
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from .models import Course, Elective, PrerequisiteRule, CareerMapping, FAQ, ChatHistory

logger = logging.getLogger(__name__)

DEPARTMENTS = {
    "Computer Science": ["CMP", "CSC", "COS"],
    "Cyber Security": ["CYB"],
    "Information Technology": ["IFT"]
}

def extract_course_code(text):
    match = re.search(r'([a-zA-Z]{3})\s*([0-9]{3})', text)
    if match:
        return f"{match.group(1).upper()}{match.group(2)}"
    return None

def extract_department(text):
    text = text.upper()
    for dept_name, codes in DEPARTMENTS.items():
        for code in codes:
            if code in text:
                return dept_name
    if "COMPUTER SCIENCE" in text: return "Computer Science"
    if "CYBER SECURITY" in text: return "Cyber Security"
    if "INFORMATION TECHNOLOGY" in text: return "Information Technology"
    return None

def handle_greeting(session_context):
    response_text = "Hello! I am ACADEMIC QUERY, your intelligent academic adviser. You can ask me about courses, prerequisites, electives, graduation requirements, or career paths. How can I help you today?"
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
        return (
            "small_talk",
            "I'm doing well, thanks for asking. I'm ready to help with courses, prerequisites, registration, GPA, graduation, or career advice."
        )

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
        "- **Prerequisites**: What you need to pass before taking advanced courses.\n"
        "- **Electives**: Recommendations based on your level and career goals.\n"
        "- **Registration**: Guidance on unit limits, add/drop periods, and timetable clashes.\n"
        "- **Graduation**: Tracking your progress towards the 160 units (120 for Direct Entry) requirement.\n"
        "- **GPA**: Explaining the 5.0 scale and how to stay in good standing.\n"
        "- **Careers**: Mapping courses to paths like Data Science or Cybersecurity.\n\n"
        "What would you like to know more about?"
    )

def handle_course_info(db, user_query, course_code, session_context):
    if course_code:
        course = db.query(Course).filter(Course.course_code == course_code).first()
        if course:
            return f"Here is the information for {course.title} ({course.course_code}): {course.description}. Credits: {course.credits}."
        return f"I'm sorry, I couldn't find any information on {course_code} in our database."
    
    dept_prompt = "" if session_context.get("department_confirmed") else " Also, please tell me your department."
    return "It seems you're asking about course options. What level are you asking about (e.g., 200 level, 300 level)?" + dept_prompt

def handle_prerequisites(db, user_query, course_code):
    level_match = re.search(r'([1-5]00)\s*level', user_query)
    if course_code:
        prereqs = db.query(PrerequisiteRule).filter(PrerequisiteRule.target_course_code == course_code).all()
        if prereqs:
            codes = [p.required_course_code for p in prereqs]
            response = f"The prerequisites for {course_code} are: {', '.join(codes)}."
            if "failed" in user_query:
                response += " Generally, you cannot register for a course if you have not passed its prerequisites. You must retake and pass the prerequisite first."
            return response
        return f"There are no required prerequisites listed for {course_code}."
    elif "failed" in user_query and "prerequisite" in user_query:
        return "No. If you failed a prerequisite, you generally need to retake and pass that prerequisite before registering for the higher-level course."
    elif "skip" in user_query and "course" in user_query:
        return "Skipping a required (compulsory) course is not allowed. All compulsory courses must be passed to qualify for graduation. If it's a prerequisite, you'll be blocked from higher-level courses."
    elif level_match:
        level_str = level_match.group(1)[0]
        courses_in_level = db.query(Course).filter(Course.course_code.like(f"%{level_str}__")).all()
        if courses_in_level:
            course_codes = [c.course_code for c in courses_in_level]
            all_rules = db.query(PrerequisiteRule).filter(PrerequisiteRule.target_course_code.in_(course_codes)).all()
            if all_rules:
                grouped = {}
                for p in all_rules:
                    grouped.setdefault(p.target_course_code, []).append(p.required_course_code)
                details = [f"- {k} requires {', '.join(v)}" for k, v in grouped.items()]
                return f"Here are the prerequisites for {level_match.group(1)} level courses:\n" + "\n".join(details)
            return f"There are no prerequisites currently recorded for {level_match.group(1)} level courses."
        return f"I couldn't find any courses for the {level_match.group(1)} level."
    return "Please specify the exact course code or academic level (e.g., '300 level') you want to check prerequisites for."

def handle_electives(db, user_query, session_context):
    if "career" in user_query and any(k in user_query for k in ["cybersecurity", "software engineering", "data science"]):
        return (
            "For career-focused electives, choose based on your target path:\n"
            "- Cybersecurity: prioritize security, networking, system security, and information defence courses.\n"
            "- Software Engineering: prioritize object-oriented programming, software engineering, databases, and web/mobile development courses.\n"
            "- Data Science: prioritize statistics, databases, data analysis, artificial intelligence, and machine learning related courses."
        )

    level_match = re.search(r'([1-5])00\s*level', user_query) or re.search(r'([1-5])00', user_query)
    electives_q = db.query(Elective)
    if level_match:
        level_digit = level_match.group(1)
        electives_q = electives_q.filter(Elective.course_code.like(f"%{level_digit}__"))

    confirmed_dept = session_context.get("department") if session_context.get("department_confirmed") else None
    if confirmed_dept:
        prefixes = DEPARTMENTS.get(confirmed_dept, [])
        if prefixes:
            or_filters = [Elective.course_code.like(f"{p}%") for p in prefixes]
            electives_q = electives_q.filter(or_(*or_filters))

    electives = electives_q.limit(10).all()
    if electives:
        items = [f"{e.course_code}: {e.title}" for e in electives]
        return "Here are some electives you can take:\n- " + "\n- ".join(items)
    return "I couldn't find any electives matching that level/department. Try specifying a level (e.g., '300 level') or your department."

def handle_registration(db, user_query, session_context):
    level_match = re.search(r'(\d{3})\s*level', user_query)
    confirmed_dept = session_context.get("department") if session_context.get("department_confirmed") else None
    
    if "how many" in user_query or "maximum" in user_query or "unit" in user_query:
        if "direct entry" in user_query:
             return "As a direct entry or transfer student into 200 Level, you are allowed to request for a maximum of 3 extra units per semester (totaling up to 28 units), subject to Senate's approval. The standard maximum is 25 units."
        return "Every student is expected to register for a minimum of 15 credit units per semester and a maximum of 25 credit units."
    
    if "extra" in user_query or "beyond" in user_query:
        return "Yes, you can typically take extra courses beyond your required load (up to the 25-unit limit). If you are a direct entry student, you can request up to 3 extra units beyond the standard maximum with Senate approval."
    
    if "compulsory" in user_query or "required" in user_query or "should i register" in user_query:
        if level_match:
            level_str = level_match.group(1)[0]
            courses = db.query(Course).filter(Course.course_code.like(f"%{level_str}__")).all()
            if courses:
                elective_codes = {e.course_code for e in db.query(Elective).all()}
                compulsory = [c for c in courses if c.course_code not in elective_codes]
                if compulsory:
                    items = [f"{c.course_code}: {c.title}" for c in compulsory[:12]]
                    dept_note = f" for {confirmed_dept}" if confirmed_dept else ""
                    return f"Here are the compulsory courses for {level_match.group(1)} level{dept_note}:\n- " + "\n- ".join(items)
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

def handle_gpa(user_query):
    if "calculated" in user_query or "calculate" in user_query or "how is" in user_query:
        return "CGPA is calculated by dividing the sum of quality points (Credit Units × Grade Points) by the total sum of credit units taken (CGPA = Σ(CR × QP) / ΣCR). We use a 5.0 scale."
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
    found_career = None
    for m in mappings:
        if m.career_path.lower() in user_query:
            found_career = m
            break
    if found_career:
        return f"To pursue a career as a {found_career.career_path}, we recommend taking {found_career.recommended_course_code}."
    
    return "We have advice for various career paths. Tell me which field you're interested in, such as Cybersecurity, Data Science, or Web Development."

def handle_fallback(db, user_query):
    # Try FAQ first
    faqs = db.query(FAQ).all()
    faq_questions = [faq.question.lower() for faq in faqs]
    matches = difflib.get_close_matches(user_query, faq_questions, n=1, cutoff=0.5)
    if matches:
        matched_q = matches[0]
        matched_faq = next(f for f in faqs if f.question.lower() == matched_q)
        return matched_faq.answer, "faq"
    
    # Try course search
    course_matches = db.query(Course).filter(
        (Course.title.ilike(f"%{user_query}%")) | 
        (Course.description.ilike(f"%{user_query}%"))
    ).limit(3).all()
    
    if course_matches:
        items = [f"{c.course_code}: {c.title}" for c in course_matches]
        return f"I couldn't find an exact answer, but here are some related courses:\n- " + "\n- ".join(items), "course_search"
    
    return "I'm not quite sure about that specific detail. Try asking about courses, prerequisites, graduation requirements, or CGPA.", "fallback"
