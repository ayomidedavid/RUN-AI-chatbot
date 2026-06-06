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
    department = Column(String(100), nullable=True)
    level = Column(Integer, nullable=True)
    semester = Column(String(20), nullable=True)
    status = Column(String(20), nullable=True)  # C = Compulsory, E = Elective

class CareerMapping(Base):
    __tablename__ = "career_mappings"
    id = Column(Integer, primary_key=True, index=True)
    career_path = Column(String(255), index=True, nullable=False)
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
    sender = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    timestamp = Column(String(50), nullable=False)

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
