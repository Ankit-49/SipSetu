import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from models import db

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Configure Database
    # Using environment variable or default to localhost
    db_uri = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/sipsetu')
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    from routes import api
    app.register_blueprint(api, url_prefix='/api')

    with app.app_context():
        db.create_all()
        # Safe migration check: add status column to job_applications if not exists
        try:
            db.session.execute(db.text("ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending' NOT NULL"))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("Migration warning (status column):", e)
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy"}), 200
        
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
