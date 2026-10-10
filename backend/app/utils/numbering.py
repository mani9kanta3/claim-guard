from datetime import date

from sqlalchemy import text

from app.extensions import db


def next_id_and_number(table_name, prefix, width):
    next_id = db.session.execute(text(f"SELECT nextval('{table_name}_id_seq')")).scalar()
    number = f"{prefix}-{date.today().year}-{next_id:0{width}d}"
    return next_id, number
