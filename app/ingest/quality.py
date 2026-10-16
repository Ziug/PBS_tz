from datetime import date, datetime
from sqlalchemy.orm import Session
from app.models import PrepRun, WeldNeed, DocRun, DataIssue

TODAY = date(2026, 10, 16)  # период данных; "будущее" = после TODAY


def classify_prep(s: Session):
    rows = s.query(PrepRun).all()
    seen = {}
    for r in rows:
        # дубликаты по record_id
        seen.setdefault(r.record_id, []).append(r)
    for rid, lst in seen.items():
        if len(lst) > 1:
            for r in lst:
                s.add(DataIssue(table_name="prep_runs", record_id=rid, source_row=r.source_row,
                                issue_type="duplicate_record", severity="high", field="record_id",
                                message=f"Дубликат record_id {rid} (строка {r.source_row})"))
    for r in rows:
        if r.fact_qty is None:
            s.add(DataIssue(table_name="prep_runs", record_id=r.record_id, source_row=r.source_row,
                            issue_type="missing_value", severity="medium", field="fact_qty",
                            message="Пустой факт"))
        if r.plan_qty is None or r.plan_qty < 0:
            s.add(DataIssue(table_name="prep_runs", record_id=r.record_id, source_row=r.source_row,
                            issue_type="invalid_value", severity="high", field="plan_qty",
                            message=f"Некорректный план: {r.plan_qty}"))
        if r.fact_qty is not None and r.fact_qty < 0:
            s.add(DataIssue(table_name="prep_runs", record_id=r.record_id, source_row=r.source_row,
                            issue_type="negative_value", severity="high", field="fact_qty",
                            message=f"Отрицательный факт: {r.fact_qty}"))
        if r.fact_qty is not None and r.plan_qty and r.fact_qty > r.plan_qty * 5:
            s.add(DataIssue(table_name="prep_runs", record_id=r.record_id, source_row=r.source_row,
                            issue_type="implausible_value", severity="medium", field="fact_qty",
                            message=f"Факт {r.fact_qty} многократно превышает план {r.plan_qty}"))
        if r.date and r.date > TODAY:
            s.add(DataIssue(table_name="prep_runs", record_id=r.record_id, source_row=r.source_row,
                            issue_type="future_date", severity="high", field="date",
                            message=f"Дата в будущем: {r.date}"))
        if r.plan_qty == 0:
            r.quality_status = "unreliable" if False else r.quality_status
    s.flush()


def classify_weld(s: Session):
    rows = s.query(WeldNeed).all()
    seen = {}
    for r in rows:
        seen.setdefault(r.record_id, []).append(r)
    for rid, lst in seen.items():
        if len(lst) > 1:
            for r in lst:
                s.add(DataIssue(table_name="weld_needs", record_id=rid, source_row=r.source_row,
                                issue_type="duplicate_record", severity="high", field="record_id",
                                message=f"Дубликат record_id {rid}"))
    for r in rows:
        if r.need_qty is None or r.need_qty < 0:
            s.add(DataIssue(table_name="weld_needs", record_id=r.record_id, source_row=r.source_row,
                            issue_type="invalid_value", severity="high", field="need_qty",
                            message=f"Некорректная потребность: {r.need_qty}"))
        if r.date and r.date > TODAY:
            s.add(DataIssue(table_name="weld_needs", record_id=r.record_id, source_row=r.source_row,
                            issue_type="future_date", severity="high", field="date",
                            message=f"Дата в будущем: {r.date}"))


def classify_docs(s: Session):
    rows = s.query(DocRun).all()
    seen = {}
    for r in rows:
        seen.setdefault(r.record_id, []).append(r)
    for rid, lst in seen.items():
        if len(lst) > 1:
            for r in lst:
                s.add(DataIssue(table_name="docs_runs", record_id=rid, source_row=r.source_row,
                                issue_type="duplicate_record", severity="high", field="record_id",
                                message=f"Дубликат record_id {rid}"))
    for r in rows:
        if r.plan_docs is None or r.plan_docs < 0:
            s.add(DataIssue(table_name="docs_runs", record_id=r.record_id, source_row=r.source_row,
                            issue_type="invalid_value", severity="high", field="plan_docs",
                            message=f"Некорректный план: {r.plan_docs}"))
        if r.fact_docs is None or r.fact_docs < 0:
            s.add(DataIssue(table_name="docs_runs", record_id=r.record_id, source_row=r.source_row,
                            issue_type="invalid_value", severity="high", field="fact_docs",
                            message=f"Некорректный факт: {r.fact_docs}"))
        if r.date and r.date > TODAY:
            s.add(DataIssue(table_name="docs_runs", record_id=r.record_id, source_row=r.source_row,
                            issue_type="future_date", severity="high", field="date",
                            message=f"Дата в будущем: {r.date}"))


def classify_all(s: Session):
    # очистить старые нерешённые issues для повторного запуска
    s.query(DataIssue).filter_by(resolved=False).delete()
    classify_prep(s)
    classify_weld(s)
    classify_docs(s)
    s.commit()
