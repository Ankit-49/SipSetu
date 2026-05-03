from flask import Blueprint, request, jsonify
from models import db, User, Applicant, Recruiter, Job, Resume, Skill, Ranking
from werkzeug.security import generate_password_hash, check_password_hash

api = Blueprint('api', __name__)

@api.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    
    if not email or not password or not role:
        return jsonify({"error": "Missing required fields"}), 400
        
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User already exists"}), 409
        
    hashed_password = generate_password_hash(password)
    
    if role == 'applicant':
        new_user = Applicant(email=email, password_hash=hashed_password, role=role)
    elif role == 'recruiter':
        new_user = Recruiter(email=email, password_hash=hashed_password, role=role)
    else:
        return jsonify({"error": "Invalid role"}), 400
        
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User registered successfully", "user_id": new_user.user_id}), 201

@api.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401
        
    return jsonify({
        "message": "Login successful",
        "user_id": user.user_id,
        "role": user.role
    }), 200

@api.route('/jobs', methods=['GET', 'POST'])
def jobs():
    if request.method == 'POST':
        data = request.get_json()
        recruiter_id = data.get('recruiter_id')
        title = data.get('title')
        skills = data.get('skills', []) # list of skill names
        
        if not recruiter_id or not title:
            return jsonify({"error": "Missing required fields"}), 400
            
        new_job = Job(recruiter_id=recruiter_id, title=title)
        
        for skill_name in skills:
            skill = Skill.query.filter_by(skill_name=skill_name).first()
            if not skill:
                skill = Skill(skill_name=skill_name)
                db.session.add(skill)
            new_job.skills.append(skill)
            
        db.session.add(new_job)
        db.session.commit()
        return jsonify({"message": "Job posted successfully"}), 201
        
    elif request.method == 'GET':
        jobs = Job.query.all()
        result = []
        for job in jobs:
            result.append({
                "job_id": job.job_id,
                "title": job.title,
                "recruiter_id": job.recruiter_id,
                "skills": [s.skill_name for s in job.skills]
            })
        return jsonify(result), 200

# Mock NLP processing for now until Spacy is fully wired up
@api.route('/resumes', methods=['POST'])
def resumes():
    # In a real scenario, we handle multipart form data for file upload
    data = request.get_json()
    applicant_id = data.get('applicant_id')
    raw_text = data.get('raw_text', '')
    
    if not applicant_id:
        return jsonify({"error": "Missing applicant_id"}), 400
        
    # TODO: Implement TF-IDF and Cosine Similarity matching here against active jobs
    
    new_resume = Resume(applicant_id=applicant_id, raw_text=raw_text)
    db.session.add(new_resume)
    db.session.commit()
    
    return jsonify({"message": "Resume uploaded successfully"}), 201
