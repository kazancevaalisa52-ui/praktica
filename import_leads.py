import csv
from datetime import datetime
from models import db, Ticket, Category

CATEGORY_MAP = {"cets": "Cets", "печать": "Печать", "по": "ПО"}


def clean_category(raw):
    key = (raw or "").strip().lower()
    return CATEGORY_MAP.get(key)


def import_leads(path):
    seen, added, skipped = set(), 0, 0
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter=";"):
            sid = int(row["source_id"])
            subject = (row["subject"] or "").strip()
            cat = clean_category(row["category"])
            if not subject or subject == "0" or cat is None:
                skipped += 1
                continue
            if sid in seen:
                skipped += 1
                continue
            seen.add(sid)
            if Ticket.query.filter_by(source_id=sid).first():
                continue
            category = Category.query.filter_by(name=cat).first()
            if not category:
                category = Category(name=cat)
                db.session.add(category)
                db.session.flush()
            db.session.add(Ticket(
                source_id=sid,
                date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                room=row["room"].strip(),
                category_id=category.id,
                subject=subject,
                status="Новая",
                service_down=row["service_down"].strip() == "1",
                affected_count=int(row["affected_count"]),
            ))
            added += 1
    db.session.commit()
    return added, skipped