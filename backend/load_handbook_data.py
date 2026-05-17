import csv
import os
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend.models import ExamRule, Conduct, Curriculum, Staff, Facility, Policy, Base

def load_csv_to_table(file_path, model_class, db: Session):
    if not os.path.exists(file_path):
        print(f"Skipping {file_path}, not found.")
        return
    
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Check if entry already exists to avoid duplicates (basic check)
            existing = db.query(model_class).filter(
                model_class.category == row['Category'], 
                model_class.detail == row['Detail']
            ).first()
            if not existing:
                db.add(model_class(category=row['Category'], detail=row['Detail']))
    db.commit()
    print(f"Loaded data from {file_path}")

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    mappings = [
        ("exam_rules.csv", ExamRule),
        ("conduct_data.csv", Conduct),
        ("curriculum_data.csv", Curriculum),
        ("staff_data.csv", Staff),
        ("facilities_data.csv", Facility),
        ("policies_data.csv", Policy)
    ]
    
    for filename, model in mappings:
        path = os.path.join(backend_dir, filename)
        load_csv_to_table(path, model, db)
    
    db.close()
    print("Handbook data population complete!")

if __name__ == "__main__":
    main()
