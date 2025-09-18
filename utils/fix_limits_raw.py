#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, MetaData, update, inspect

# point at your real DB file
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE, "instance", "video_app.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)
print("Connecting to:", DATABASE_URL)
print("Tables I see:", inspect(engine).get_table_names())

meta = MetaData()
meta.reflect(bind=engine)

tables_to_fix = [t for t in ("user", "users") if t in meta.tables]

with engine.begin() as conn:
    total = 0
    for tbl_name in tables_to_fix:
        users_tbl = meta.tables[tbl_name]
        stmt = (
            update(users_tbl)
            .where(users_tbl.c.projects_limit.is_(None))
            .values(projects_limit=3)
        )
        res = conn.execute(stmt)
        print(f" → Fixed {res.rowcount} rows in “{tbl_name}”")
        total += res.rowcount

print(f"Done. Total fixed: {total}")