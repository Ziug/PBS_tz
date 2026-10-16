from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, Float, Text, Boolean
from app.database import Base


class PrepRun(Base):
    __tablename__ = "prep_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    batch_id = Column(String, nullable=False, index=True)
    employee = Column(String, nullable=False)
    plan_qty = Column(Integer, nullable=False)
    fact_qty = Column(Integer, nullable=True)
    source_row = Column(Integer, nullable=False)
    import_batch = Column(String, nullable=False)
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    quality_status = Column(String, default="pending", nullable=False)
    notes = Column(Text, nullable=True)
    user_edited = Column(Boolean, default=False, nullable=False)


class WeldNeed(Base):
    __tablename__ = "weld_needs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    batch_id = Column(String, nullable=False, index=True)
    need_qty = Column(Integer, nullable=False)
    source_row = Column(Integer, nullable=False)
    import_batch = Column(String, nullable=False)
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    quality_status = Column(String, default="pending", nullable=False)
    notes = Column(Text, nullable=True)
    user_edited = Column(Boolean, default=False, nullable=False)


class DocRun(Base):
    __tablename__ = "docs_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    employee = Column(String, nullable=False)
    plan_docs = Column(Integer, nullable=False)
    fact_docs = Column(Integer, nullable=False)
    source_row = Column(Integer, nullable=False)
    import_batch = Column(String, nullable=False)
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    quality_status = Column(String, default="pending", nullable=False)
    notes = Column(Text, nullable=True)
    user_edited = Column(Boolean, default=False, nullable=False)


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String, nullable=False)
    file_hash = Column(String, nullable=False, unique=True)
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    row_count = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    message = Column(Text, nullable=True)


class FormulaSnapshot(Base):
    __tablename__ = "formula_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sheet = Column(String, nullable=False)
    label = Column(String, nullable=False)
    formula = Column(String, nullable=True)
    cached_value = Column(String, nullable=True)
    computable = Column(Boolean, nullable=False, default=False)
    note = Column(Text, nullable=True)
    import_batch = Column(String, nullable=False)
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DataIssue(Base):
    __tablename__ = "data_issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String, nullable=False, index=True)
    record_id = Column(String, nullable=True, index=True)
    source_row = Column(Integer, nullable=True)
    issue_type = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False)
    field = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved = Column(Boolean, default=False, nullable=False)
