import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import func
from app.database import SessionLocal, init_db
from app.models import PrepRun, WeldNeed, DocRun, FormulaSnapshot

def test_counts():
    init_db()
    s = SessionLocal()
    assert s.query(PrepRun).count() == 9
    assert s.query(WeldNeed).count() == 8
    assert s.query(DocRun).count() == 6
    assert s.query(FormulaSnapshot).count() == 3
    s.close()

def test_types():
    s = SessionLocal()
    p = s.query(PrepRun).first()
    assert p.plan_qty == 100
    assert p.fact_qty in (None, 90)
    assert p.date is not None
    s.close()

def test_duplicate_record_preserved():
    s = SessionLocal()
    assert s.query(PrepRun).filter_by(record_id="P-005").count() == 2
    s.close()
