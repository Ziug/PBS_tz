import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import SessionLocal, init_db
from app.ingest.quality import classify_all
from app.models import DataIssue
from sqlalchemy import func

if __name__ == "__main__":
    init_db()
    s = SessionLocal()
    classify_all(s)
    print("ISSUE COUNTS:")
    for t, c in s.query(DataIssue.issue_type, func.count()).group_by(DataIssue.issue_type).all():
        print(f"  {t}: {c}")
    print("TOTAL", s.query(DataIssue).count())
    s.close()
