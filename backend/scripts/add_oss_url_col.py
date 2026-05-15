"""Add oss_url column to files table if not exists."""
import os
from sqlalchemy import create_engine, text

db_url = os.environ.get('DATABASE_URL', 'postgresql://opsvideo:opsvideo@db:5432/opsvideo')
sync_url = db_url.replace('+asyncpg', '')
engine = create_engine(sync_url)

with engine.connect() as conn:
    result = conn.execute(
        text("SELECT column_name FROM information_schema.columns WHERE table_name='files' AND column_name='oss_url'")
    ).fetchone()
    if result:
        print("oss_url column already exists")
    else:
        conn.execute(text("ALTER TABLE files ADD COLUMN oss_url TEXT"))
        conn.commit()
        print("Added oss_url column")
