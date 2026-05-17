import os
import sys

try:
    from backend.database import SessionLocal
    from backend.models import FAQ
except ImportError:
    # Allow direct execution from the backend directory
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from database import SessionLocal
    from models import FAQ

db = SessionLocal()
existing = db.query(FAQ).filter(FAQ.question.like('%units must i do before i graduate%')).first()

if not existing:
    new_faq = FAQ(
        question='How many units must I do before I graduate?',
        answer='To graduate, you generally must complete a minimum of 120 credit units for a standard 4-year degree programme, but this may vary depending on your specific department.'
    )
    db.add(new_faq)
    db.commit()
    print('FAQ inserted successfully.')
else:
    print('FAQ already exists.')
db.close()
