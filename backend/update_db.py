from app import create_app
from models import db
from sqlalchemy import text
app = create_app()
with app.app_context():
    try:
        # Add columns to users table
        db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(255)"))
        db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20)"))
        db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS location VARCHAR(255)"))
        
        # Add columns to recruiters table
        db.session.execute(text("ALTER TABLE recruiters ADD COLUMN IF NOT EXISTS company VARCHAR(255)"))
        db.session.execute(text("ALTER TABLE recruiters ADD COLUMN IF NOT EXISTS job_title VARCHAR(255)"))
        
        db.session.commit()
        print("Database schema updated successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error updating database: {e}")
