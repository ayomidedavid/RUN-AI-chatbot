import re
import difflib
import logging
import json
import os
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from dotenv import load_dotenv
load_dotenv()

from .database import get_db, engine, Base
from .models import Course, CareerMapping, FAQ, ChatHistory
from .ml_model import IntentClassifier
from . import chat_handlers
from . import llm_service
import pickle

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

logging.basicConfig(
    filename='chatbot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

import faiss

app = FastAPI(title="ACADEMIC QUERY")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def preload_models():
    logger.info("Pre-loading AI models into memory...")
    llm_service.get_generator()
    load_retrieval()
    logger.info("All AI models pre-loaded successfully! Server is ready.")

RETRIEVAL_MODEL = None
FAISS_INDEX = None
CHUNKS = None
RETRIEVAL_DIM = None
RETRIEVAL_LOAD_ATTEMPTED = False

def load_retrieval(out_dir=None, model_name='all-MiniLM-L6-v2'):
    global RETRIEVAL_MODEL, FAISS_INDEX, CHUNKS, RETRIEVAL_DIM, RETRIEVAL_LOAD_ATTEMPTED
    RETRIEVAL_LOAD_ATTEMPTED = True
    try:
        from sentence_transformers import SentenceTransformer
        base = Path(__file__).resolve().parent
        idx_path = base / 'faiss.index'
        chunks_path = base / 'chunks.pkl'
        if idx_path.exists() and chunks_path.exists():
            local_model = base / 'models' / 'all-MiniLM-L6-v2'
            if local_model.exists():
                os.environ['HF_HUB_OFFLINE'] = '1'
                os.environ['TRANSFORMERS_OFFLINE'] = '1'
                RETRIEVAL_MODEL = SentenceTransformer(str(local_model))
            else:
                RETRIEVAL_MODEL = SentenceTransformer(model_name)
            FAISS_INDEX = faiss.read_index(str(idx_path))
            with open(chunks_path, 'rb') as f:
                CHUNKS = pickle.load(f)
            RETRIEVAL_DIM = RETRIEVAL_MODEL.get_sentence_embedding_dimension()
            print('Loaded retrieval index with', len(CHUNKS), 'chunks')
    except Exception as e:
        logger.exception('Failed to load retrieval artifacts')

@app.get('/api/retrieve')
def api_retrieve(q: str = Query(...), k: int = 3):
    items = retrieve(q, k=k)
    return {"query": q, "results": [{"text": t, "score": s} for t, s in items]}

def verify_admin(x_admin_password: str = Header(None)):
    if x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post('/api/admin/rebuild_index')
def api_rebuild_index(db: Session = Depends(get_db), _: None = Depends(verify_admin)):
    try:
        from . import index_documents
        index_documents.build_index()
        load_retrieval()
        return {"message": "Index rebuilt and reloaded"}
    except Exception as e:
        logger.exception('Failed to rebuild index')
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/admin/retrain_model')
def api_retrain_model(_: None = Depends(verify_admin)):
    try:
        from .ml_model import IntentClassifier
        clf = IntentClassifier()
        clf.train_and_save()
        global intent_classifier
        intent_classifier.load_model()
        return {"message": "Intent model retrained and reloaded"}
    except Exception as e:
        logger.exception('Failed to retrain model')
        raise HTTPException(status_code=500, detail=str(e))

def retrieve(query, k=3):
    if not RETRIEVAL_LOAD_ATTEMPTED:
        load_retrieval()
    if FAISS_INDEX is None or RETRIEVAL_MODEL is None or CHUNKS is None:
        return []
    emb = RETRIEVAL_MODEL.encode([query], convert_to_numpy=True)
    import numpy as np
    faiss.normalize_L2(emb)
    D, I = FAISS_INDEX.search(emb, k)
    results = []
    for score, idx in zip(D[0], I[0]):
        if idx < 0 or idx >= len(CHUNKS):
            continue
        results.append((CHUNKS[idx], float(score)))
    return results

Base.metadata.create_all(bind=engine)
user_sessions = {}

@app.get("/")
def read_root():
    return {"message": "ACADEMIC QUERY API is online. Use the frontend or /api/chat to interact."}

intent_classifier = IntentClassifier()
intent_classifier.load_model()

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    user_profile: Optional[dict] = None

class ChatResponse(BaseModel):
    intent: str
    response: str
    data: Optional[dict] = None
    session_id: Optional[str] = None
    context: Optional[dict] = None

class CourseCreate(BaseModel):
    course_code: str
    title: str
    description: Optional[str] = None
    credits: Optional[int] = None

class CourseUpdate(BaseModel):
    title: str
    description: Optional[str] = None
    credits: Optional[int] = None
    new_course_code: Optional[str] = None

class GPACalculationRequest(BaseModel):
    courses: List[dict]

class GPACalculationResponse(BaseModel):
    gpa: float
    total_quality_points: float
    total_credits: int
    breakdown: List[dict]

GRADE_POINTS = {
    "A": 5, "B": 4, "C": 3, "D": 2, "E": 1, "F": 0
}

def score_to_grade(score):
    if score >= 70: return "A"
    if score >= 60: return "B"
    if score >= 50: return "C"
    if score >= 45: return "D"
    if score >= 40: return "E"
    return "F"

@app.post("/api/gpa/calculate", response_model=GPACalculationResponse)
def calculate_gpa(request: GPACalculationRequest):
    total_qp = 0.0
    total_credits = 0
    breakdown = []
    for c in request.courses:
        credits = c.get("credits", 0)
        score = c.get("score", 0)
        grade = c.get("grade", score_to_grade(score))
        gp = GRADE_POINTS.get(grade.upper(), 0)
        qp = credits * gp
        total_qp += qp
        total_credits += credits
        breakdown.append({
            "course": c.get("course", "Unknown"),
            "credits": credits,
            "score": score,
            "grade": grade.upper(),
            "grade_point": gp,
            "quality_point": qp
        })
    gpa = round(total_qp / total_credits, 2) if total_credits > 0 else 0.0
    return GPACalculationResponse(
        gpa=gpa,
        total_quality_points=total_qp,
        total_credits=total_credits,
        breakdown=breakdown
    )

@app.get("/api/courses")
def get_all_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).order_by(Course.level, Course.semester, Course.course_code).all()
    result = []
    for c in courses:
        dept = c.department or chat_handlers.extract_department(c.course_code) or "Other"
        level = c.level or 0
        result.append({
            "course_code": c.course_code,
            "title": c.title,
            "credits": c.credits,
            "department": dept,
            "level": f"{level // 100}00 Level" if level else "Unknown",
            "semester": c.semester or "Unknown",
            "status": c.status or "Unknown"
        })
    return {"courses": result}

@app.get("/api/admin/status")
def get_system_status(db: Session = Depends(get_db), _: None = Depends(verify_admin)):
    return {
        "counts": {
            "courses": db.query(Course).count(),
            "faqs": db.query(FAQ).count(),
            "careers": db.query(CareerMapping).count(),
            "chat_history": db.query(ChatHistory).count()
        },
        "system": {
            "faiss_index": FAISS_INDEX is not None,
            "retrieval_model": RETRIEVAL_MODEL is not None,
            "intent_classifier": intent_classifier.pipeline is not None
        }
    }

@app.post("/api/admin/courses")
def create_course(course: CourseCreate, db: Session = Depends(get_db), _: None = Depends(verify_admin)):
    existing = db.query(Course).filter(Course.course_code == course.course_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Course already exists")
    new_course = Course(**course.dict())
    db.add(new_course)
    db.commit()
    return {"message": "Course created successfully"}

@app.get("/api/faqs")
def get_faqs(db: Session = Depends(get_db)):
    return {"faqs": db.query(FAQ).all()}

@app.post("/api/admin/faqs")
def create_faq(faq: dict, db: Session = Depends(get_db), _: None = Depends(verify_admin)):
    new_faq = FAQ(question=faq['question'], answer=faq['answer'])
    db.add(new_faq)
    db.commit()
    return {"message": "FAQ created"}

@app.delete("/api/admin/faqs/{faq_id}")
def delete_faq(faq_id: int, db: Session = Depends(get_db), _: None = Depends(verify_admin)):
    db.query(FAQ).filter(FAQ.id == faq_id).delete()
    db.commit()
    return {"message": "FAQ deleted"}

@app.get("/api/careers")
def get_careers(db: Session = Depends(get_db)):
    return {"careers": db.query(CareerMapping).all()}

@app.post("/api/admin/careers")
def create_career(mapping: dict, db: Session = Depends(get_db), _: None = Depends(verify_admin)):
    new_m = CareerMapping(career_path=mapping['career_path'], recommended_course_code=mapping['recommended_course_code'])
    db.add(new_m)
    db.commit()
    return {"message": "Career mapping created"}

@app.delete("/api/admin/careers/{mapping_id}")
def delete_career(mapping_id: int, db: Session = Depends(get_db), _: None = Depends(verify_admin)):
    db.query(CareerMapping).filter(CareerMapping.id == mapping_id).delete()
    db.commit()
    return {"message": "Career mapping deleted"}

@app.get("/api/admin/handbook/{category}")
def get_handbook_data(category: str, db: Session = Depends(get_db), _: None = Depends(verify_admin)):
    from .models import ExamRule, Conduct, Policy, Staff
    table_map = {"exams": ExamRule, "conduct": Conduct, "policies": Policy, "staff": Staff}
    if category not in table_map:
        raise HTTPException(status_code=400, detail="Invalid category")
    return {"data": db.query(table_map[category]).all()}

@app.post("/api/chat", response_model=ChatResponse)
def handle_chat(request: ChatRequest, db: Session = Depends(get_db)):
    user_query = request.query.lower()
    session_id = request.session_id or "default"
    if session_id not in user_sessions:
        last_chat = db.query(ChatHistory).filter(ChatHistory.session_id == session_id).order_by(ChatHistory.id.desc()).first()
        if last_chat and last_chat.context:
            try:
                user_sessions[session_id] = json.loads(last_chat.context)
            except:
                user_sessions[session_id] = {"last_intent": None, "last_topic": None, "department": None, "department_confirmed": False, "history": []}
        else:
            user_sessions[session_id] = {
                "last_intent": None,
                "last_topic": None,
                "department": None,
                "department_confirmed": False,
                "history": []
            }

    session_context = user_sessions[session_id]

    if request.user_profile:
        if request.user_profile.get("department"):
            session_context["department"] = request.user_profile.get("department")
            session_context["department_confirmed"] = True
        session_context["user_profile"] = request.user_profile

    chat_history_str = ""
    for msg in session_context.get("history", []):
        sender_name = "User" if msg["sender"] == "user" else "Assistant"
        chat_history_str += f"{sender_name}: {msg['message']}\n"

    processed_query = chat_handlers.normalize_multilingual_query(user_query)
    if any(p in user_query.split() for p in ['it', 'that', 'this', 'its']) and session_context.get("last_topic"):
        processed_query = user_query.replace('it', session_context["last_topic"]).replace('that', session_context["last_topic"])
        logger.info(f"Resolved context: '{user_query}' -> '{processed_query}'")

    try:
        entry = ChatHistory(
            session_id=session_id,
            sender="user",
            message=request.query,
            context=json.dumps(session_context),
            timestamp=datetime.now().isoformat()
        )
        db.add(entry)
        db.commit()
    except Exception:
        logger.exception("Failed to save user chat")

    response_text = ""
    data_payload = {}
    context_info = {}

    small_talk = chat_handlers.handle_small_talk(user_query, session_context)
    if small_talk:
        predicted_intent, response_text = small_talk
    else:
        predicted_intent = intent_classifier.predict(processed_query)
    logger.info(f"Session: {session_id} | Intent: {predicted_intent}")

    course_code = chat_handlers.extract_course_code(processed_query, db)
    if course_code:
        session_context["last_topic"] = course_code
        if predicted_intent not in ["course_registration", "gpa", "graduation", "career", "electives"]:
            predicted_intent = "course_info"

    detected_dept = chat_handlers.extract_department(processed_query)
    is_department_statement = (
        predicted_intent == "department_info"
        or "my department" in user_query
        or "i am in" in user_query
        or "i'm in" in user_query
        or "i study" in user_query
        or "student" in user_query
    )

    if response_text:
        pass

    elif detected_dept and not session_context.get("department_confirmed") and is_department_statement:
        response_text = f"I see you mentioned {detected_dept}. Just to confirm, is that your department?"
        session_context["department"] = detected_dept
        predicted_intent = "department_confirmation_request"

    elif user_query in ["yes", "yeah", "correct", "yep"] and session_context.get("department") and not session_context.get("department_confirmed"):
        response_text = f"Great! I've noted that you are in the {session_context['department']} department. How can I help you today?"
        session_context["department_confirmed"] = True

    elif predicted_intent == "greeting":
        response_text = chat_handlers.handle_greeting(session_context)

    elif predicted_intent == "course_info":
        response_text = chat_handlers.handle_course_info(db, processed_query, course_code, session_context)

    elif predicted_intent == "electives":
        response_text = chat_handlers.handle_electives(db, processed_query, session_context)

    elif predicted_intent == "career":
        response_text = chat_handlers.handle_career(db, processed_query)

    elif predicted_intent == "gpa":
        response_text = chat_handlers.handle_gpa(processed_query)

    elif predicted_intent == "timetable":
        response_text = chat_handlers.handle_timetable(db, processed_query, session_context)

    elif predicted_intent == "graduation":
        response_text = chat_handlers.handle_graduation(db, processed_query)

    elif predicted_intent == "capabilities":
        response_text = chat_handlers.handle_capabilities(session_context)

    elif predicted_intent in ["course_registration", "course_management"]:
        response_text = chat_handlers.handle_registration(db, processed_query, session_context)

    elif predicted_intent == "department_info":
        if detected_dept:
            response_text = f"I see you are in the {detected_dept} department. How can I assist you with your studies?"
            session_context["department"] = detected_dept
            session_context["department_confirmed"] = True
        else:
            response_text = "Which department are you in? We currently support a wide range of departments including Computer Science, Cyber Security, Software Engineering, IT, etc."

    else:
        if "department" in user_query or "study" in user_query:
            common_depts = ["medicine", "nursing", "law"]
            if any(d in user_query for d in common_depts):
                response_text = "I'm sorry, but my current scope is focused on computing, engineering, and sciences. I don't have information for other departments yet."
            else:
                response_text, source = chat_handlers.handle_fallback(db, user_query)
        else:
            response_text, source = chat_handlers.handle_fallback(db, user_query)

        context_info["source"] = "fallback"
        if response_text == "" or predicted_intent in ["unknown", "fallback"]:
            retrieved = retrieve(request.query, k=3)
            if retrieved:
                context_info['retrieved'] = [{'text': r[0], 'score': r[1]} for r in retrieved]
                response_text = "Related information found in course catalog:\n" + "\n\n".join([r[0] for r in retrieved])
                predicted_intent = "fallback" # Enforce generative response
            else:
                if response_text == "":
                    response_text = "I'm not quite sure how to answer that. Could you try rephrasing or ask about courses, registration, or graduation?"

    if predicted_intent in ["unknown", "fallback"]:
        final_response_text = llm_service.generate_conversational_response(
            user_query=user_query,
            factual_context=response_text,
            intent=predicted_intent,
            chat_history=chat_history_str
        )
    else:
        final_response_text = response_text

    session_context.update({
        "last_intent": predicted_intent,
        "last_query": user_query,
        "timestamp": datetime.now().isoformat()
    })

    try:
        bot_entry = ChatHistory(
            session_id=session_id,
            sender="bot",
            message=final_response_text,
            context=json.dumps(session_context),
            timestamp=datetime.now().isoformat()
        )
        db.add(bot_entry)
        db.commit()
        session_context["history"].append({"sender": "bot", "message": final_response_text, "timestamp": bot_entry.timestamp})
    except Exception:
        logger.exception("Failed to save bot chat")

    data_payload["thought_process"] = response_text

    return ChatResponse(
        intent=predicted_intent,
        response=final_response_text,
        data=data_payload,
        session_id=session_id,
        context={}
    )
