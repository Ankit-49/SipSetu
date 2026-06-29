"""
Migration script to add new columns to the jobs table.
Run this once: python update_db_v2.py
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

columns_to_add = [
    ("description", "TEXT"),
    ("location", "VARCHAR(255)"),
    ("job_type", "VARCHAR(50)"),
    ("experience_level", "VARCHAR(50)"),
    ("salary_min", "FLOAT"),
    ("salary_max", "FLOAT"),
]

for col_name, col_type in columns_to_add:
    try:
        cur.execute(f"ALTER TABLE jobs ADD COLUMN IF NOT EXISTS {col_name} {col_type};")
        print(f"[OK] Added column: {col_name}")
    except Exception as e:
        print(f"[FAIL] Failed to add {col_name}: {e}")
        conn.rollback()

conn.commit()
cur.close()
conn.close()
print("\nMigration complete.")
