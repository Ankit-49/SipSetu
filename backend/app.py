import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from models import db
from config import Config

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Load configuration from Config class
    app.config.from_object(Config)

    # Configure Database — read from environment AFTER load_dotenv() so
    # the .env file takes effect (Config is evaluated at import time,
    # before load_dotenv runs, so its default is always used).
    db_url = os.environ.get('DATABASE_URL') or Config.DATABASE_URL
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from routes import api
    app.register_blueprint(api, url_prefix='/api')

    with app.app_context():
        db.create_all()
        # Safe migration check: add status column to job_applications if not exists
        try:
            db.session.execute(db.text("ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending' NOT NULL"))
            db.session.execute(db.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image TEXT"))
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

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
