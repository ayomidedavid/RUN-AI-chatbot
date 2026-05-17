from sqlalchemy import Column, Integer, String, Text, ForeignKey

try:
    from .database import Base
except ImportError:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from database import Base

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    credits = Column(Integer, nullable=True)

class Elective(Base):
    __tablename__ = "electives"
    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    semester_offered = Column(String(50), nullable=True)

class PrerequisiteRule(Base):
    __tablename__ = "prerequisites"
    id = Column(Integer, primary_key=True, index=True)
    target_course_code = Column(String(20), ForeignKey("courses.course_code"), nullable=False)
    required_course_code = Column(String(20), ForeignKey("courses.course_code"), nullable=False)

class CareerMapping(Base):
    __tablename__ = "career_mappings"
    id = Column(Integer, primary_key=True, index=True)
    career_path = Column(String(255), index=True, nullable=False) # e.g., 'Data Scientist', 'Software Engineer'
    recommended_course_code = Column(String(20), nullable=False)

class FAQ(Base):
    __tablename__ = "faqs"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    sender = Column(String(20), nullable=False)  # 'user' or 'bot'
    message = Column(Text, nullable=False)
    context = Column(Text, nullable=True) # JSON string of identified context (course_code, department, etc.)
    timestamp = Column(String(50), nullable=False)

# ----------------------------------------------------------------------
# New models for handbook sections (CSV data loaded by load_handbook_sections.py)
# ----------------------------------------------------------------------
class ExamRule(Base):
    __tablename__ = "exam_rules"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False)
    detail = Column(Text, nullable=False)

class Conduct(Base):
    __tablename__ = "conduct"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False)
    detail = Column(Text, nullable=False)

class Curriculum(Base):
    __tablename__ = "curriculum"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False)
    detail = Column(Text, nullable=False)

class Staff(Base):
    __tablename__ = "staff"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False)
    detail = Column(Text, nullable=False)

class Facility(Base):
    __tablename__ = "facilities"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False)
    detail = Column(Text, nullable=False)

class Policy(Base):
    __tablename__ = "policies"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False)
    detail = Column(Text, nullable=False)

