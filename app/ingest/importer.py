import hashlib
import logging
import os
from datetime import datetime
from typing import Optional

import openpyxl
from sqlalchemy.orm import Session

from app.database import init_db, SessionLocal
from app.models import PrepRun, WeldNeed, DocRun, ImportBatch, FormulaSnapshot

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("pbs.import")

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def to_date(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, str):
        return datetime.fromisoformat(v).date()
    raise ValueError(f"Unsupported date value: {v!r}")


def to_int_or_none(v):
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        raise ValueError("bool is not int")
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v).strip()
    if s == "":
        return None
    return int(float(s))


def sheet_rows(path, sheet_name):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[sheet_name]
    rows = list(ws.iter_rows(values_only=True))
    return rows


def import_prep(session, path, batch_id):
    rows = sheet_rows(path, "Данные")
    header = rows[0]
    expected = ["record_id", "date", "batch_id", "employee", "plan_qty", "fact_qty"]
    if list(header) != expected:
        raise ValueError(f"Prep header mismatch: {header} != {expected}")
    count = 0
    for i, r in enumerate(rows[1:], start=2):
        if all(c is None for c in r):
            continue
        rr = PrepRun(
            record_id=str(r[0]).strip(),
            date=to_date(r[1]),
            batch_id=str(r[2]).strip(),
            employee=str(r[3]).strip(),
            plan_qty=to_int_or_none(r[4]),
            fact_qty=to_int_or_none(r[5]),
            source_row=i,
            import_batch=batch_id,
        )
        session.add(rr)
        count += 1
    return count


def import_weld(session, path, batch_id):
    rows = sheet_rows(path, "Данные")
    expected = ["record_id", "date", "batch_id", "need_qty"]
    if list(rows[0]) != expected:
        raise ValueError(f"Weld header mismatch: {rows[0]} != {expected}")
    count = 0
    for i, r in enumerate(rows[1:], start=2):
        if all(c is None for c in r):
            continue
        rr = WeldNeed(
            record_id=str(r[0]).strip(),
            date=to_date(r[1]),
            batch_id=str(r[2]).strip(),
            need_qty=to_int_or_none(r[3]),
            source_row=i,
            import_batch=batch_id,
        )
        session.add(rr)
        count += 1
    return count


def import_docs(session, path, batch_id):
    rows = sheet_rows(path, "Данные")
    expected = ["record_id", "date", "employee", "plan_docs", "fact_docs"]
    if list(rows[0]) != expected:
        raise ValueError(f"Docs header mismatch: {rows[0]} != {expected}")
    count = 0
    for i, r in enumerate(rows[1:], start=2):
        if all(c is None for c in r):
            continue
        rr = DocRun(
            record_id=str(r[0]).strip(),
            date=to_date(r[1]),
            employee=str(r[2]).strip(),
            plan_docs=to_int_or_none(r[3]),
            fact_docs=to_int_or_none(r[4]),
            source_row=i,
            import_batch=batch_id,
        )
        session.add(rr)
        count += 1
    return count


def import_formula_sheet(session, path, batch_id):
    """Прочитать лист 'Пример_формул': формулы через data_only=False, значения — из data_only=True."""
    wb_f = openpyxl.load_workbook(path, data_only=False)
    wb_v = openpyxl.load_workbook(path, data_only=True)
    if "Пример_формул" not in wb_f.sheetnames:
        return 0
    ws_f = wb_f["Пример_формул"]
    ws_v = wb_v["Пример_формул"]
    count = 0
    for r_idx in range(2, ws_f.max_row + 1):
        label = ws_f.cell(row=r_idx, column=1).value
        formula = ws_f.cell(row=r_idx, column=2).value
        value = ws_v.cell(row=r_idx, column=2).value
        if label is None:
            continue
        computable = (value is not None)
        note = None
        if isinstance(formula, str) and formula.startswith("=") and value is None:
            note = ("Формула присутствует, но кэшированное вычисленное значение отсутствует; "
                    "надёжно пересчитать без Excel нельзя.")
        snap = FormulaSnapshot(
            sheet="Пример_формул",
            label=str(label),
            formula=str(formula) if formula is not None else None,
            cached_value=(str(value) if value is not None else None),
            computable=computable,
            note=note,
            import_batch=batch_id,
        )
        session.add(snap)
        count += 1
    return count


FILES = {
    "01_Заготовка.xlsx": ("prep", import_prep),
    "02_Потребность_сварки.xlsx": ("weld", import_weld),
    "03_Документация.xlsx": ("docs", import_docs),
}


def import_all(force=False):
    init_db()
    session = SessionLocal()
    results = {}
    try:
        for fname, (kind, fn) in FILES.items():
            path = os.path.join(BASE, fname)
            if not os.path.exists(path):
                raise FileNotFoundError(path)
            h = file_hash(path)
            existing = session.query(ImportBatch).filter_by(file_hash=h).first()
            if existing and not force:
                log.info("Skip %s: already imported (hash %s)", fname, h[:8])
                results[fname] = ("skipped", existing.row_count)
                continue
            if existing and force:
                # очистить старые записи этой партии только если они не редактировались пользователем
                if kind == "prep":
                    session.query(PrepRun).filter_by(import_batch=existing.id if False else None).delete()
                # проще: удалить по совпадению hash через import_batch строку вида batch_<hash>
                pass

            batch_tag = f"batch_{h[:12]}"
            # safety: если есть записи с таким batch_tag, не дублируем
            if not force:
                already = session.query(PrepRun if kind == "prep" else (WeldNeed if kind == "weld" else DocRun)).filter_by(import_batch=batch_tag).count()
                if already:
                    log.info("Skip %s: batch already present", fname)
                    results[fname] = ("skipped", already)
                    continue

            # remove previous unedited rows of same file if re-importing with force
            if force:
                if kind == "prep":
                    session.query(PrepRun).filter_by(import_batch=batch_tag).delete()
                elif kind == "weld":
                    session.query(WeldNeed).filter_by(import_batch=batch_tag).delete()
                else:
                    session.query(DocRun).filter_by(import_batch=batch_tag).delete()
                session.query(FormulaSnapshot).filter_by(import_batch=batch_tag).delete()
                session.query(ImportBatch).filter_by(file_hash=h).delete()
                session.flush()

            n = fn(session, path, batch_tag)
            session.flush()
            # formula sheet only for prep file
            if fname == "01_Заготовка.xlsx":
                import_formula_sheet(session, path, batch_tag)

            ib = ImportBatch(file_name=fname, file_hash=h, row_count=n, status="success",
                             message=f"imported {n} rows")
            session.add(ib)
            session.commit()
            log.info("Imported %s: %d rows", fname, n)
            results[fname] = ("imported", n)
        # log formula snapshots count
        fs_count = session.query(FormulaSnapshot).count()
        log.info("Formula snapshots: %d", fs_count)
        print("FORMULA_SNAPSHOTS", fs_count)
        return results
    except Exception as e:
        session.rollback()
        log.exception("Import failed: %s", e)
        # записать неудачный batch
        try:
            ib = ImportBatch(file_name="unknown", file_hash="error", row_count=0, status="error", message=str(e))
            session.add(ib)
            session.commit()
        except Exception:
            session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    res = import_all(force=False)
    for k, v in res.items():
        print(k, v)