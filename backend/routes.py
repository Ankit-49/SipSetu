from flask import Blueprint, request, jsonify
from models import db, User, Applicant, Recruiter, Job, Resume, Skill, Ranking
from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from sqlalchemy import func
import fitz  # PyMuPDF
import os

api = Blueprint('api', __name__)

# ============ UTILITY FUNCTIONS ============

def extract_skills_from_text(text):
    """
    Extract skills from resume text using simple keyword matching.
    Returns a list of skill names found in the text.
    """
    if not text:
        return []
    
    text_lower = text.lower()
    common_skills = [
        'python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'go', 'rust', 'php', 'ruby',
        'react', 'angular', 'vue', 'svelte', 'node.js', 'express', 'django', 'flask', 'fastapi',
        'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'graphql', 'rest api',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'github', 'gitlab',
        'html', 'css', 'tailwind', 'bootstrap', 'sass', 'webpack', 'vite',
        'machine learning', 'deep learning', 'nlp', 'computer vision', 'tensorflow', 'pytorch',
        'design', 'figma', 'ui', 'ux', 'product', 'agile', 'scrum', 'jira',
        'communication', 'leadership', 'teamwork', 'problem solving', 'critical thinking'
    ]
    
    found_skills = []
    for skill in common_skills:
        if skill in text_lower:
            found_skills.append(skill)
    
    return found_skills

def calculate_match_score(resume_skills_list, job_skills_list):
    """
    Calculate similarity score between resume skills and job skills using TF-IDF.
    Returns a score between 0 and 100.
    """
    if not job_skills_list:
        return 0.0
    
    if not resume_skills_list:
        return 0.0
    
    resume_set = set([s.lower() for s in resume_skills_list])
    job_set = set([s.lower() for s in job_skills_list])
    
    if len(job_set) == 0:
        return 0.0
    
    # Jaccard similarity
    intersection = len(resume_set.intersection(job_set))
    union = len(resume_set.union(job_set))
    
    if union == 0:
        return 0.0
    
    score = (intersection / union) * 100
    return round(score, 2)

def create_rankings_for_resume(resume_id, applicant_id):
    """
    Create ranking entries for a new resume against all active jobs.
    """
    resume = Resume.query.get(resume_id)
    if not resume:
        return
    
    all_jobs = Job.query.all()
    
    for job in all_jobs:
        resume_skills = [s.skill_name for s in resume.skills]
        job_skills = [s.skill_name for s in job.skills]
        score = calculate_match_score(resume_skills, job_skills)
        
        existing_ranking = Ranking.query.filter_by(job_id=job.job_id, resume_id=resume_id).first()
        if existing_ranking:
            existing_ranking.matching_score = score
        else:
            ranking = Ranking(job_id=job.job_id, resume_id=resume_id, matching_score=score)
            db.session.add(ranking)
    
    db.session.commit()

def format_job(job):
    """Serialize a Job object to a dict."""
    salary = None
    if job.salary_min and job.salary_max:
        salary = f"Rs.{int(job.salary_min)}-{int(job.salary_max)} LPA"
    elif job.salary_min:
        salary = f"Rs.{int(job.salary_min)}+ LPA"
    
    posted_at = job.created_at.isoformat() if job.created_at else None
    
    return {
        "job_id": str(job.job_id),
        "title": job.title,
        "description": job.description or "",
        "location": job.location or "",
        "job_type": job.job_type or "",
        "experience_level": job.experience_level or "",
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "salary": salary,
        "recruiter_id": str(job.recruiter_id),
        "recruiter_name": job.recruiter.name or "",
        "recruiter_company": job.recruiter.company or "",
        "created_at": posted_at,
        "skills": [s.skill_name for s in job.skills]
    }

# ============ AUTHENTICATION ROUTES ============

@api.route('/auth/register', methods=['POST'])
def register():
    """Register a new user (applicant or recruiter)"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    name = data.get('name')
    
    if not email or not password or not role:
        return jsonify({"error": "Missing required fields"}), 400
        
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User already exists"}), 409
    
    if role not in ['applicant', 'recruiter']:
        return jsonify({"error": "Invalid role"}), 400
        
    hashed_password = generate_password_hash(password)
    
    if role == 'applicant':
        new_user = Applicant(email=email, name=name, password_hash=hashed_password, role=role)
    else:
        new_user = Recruiter(email=email, name=name, password_hash=hashed_password, role=role)
        
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User registered successfully", "user_id": str(new_user.user_id), "role": role}), 201

@api.route('/auth/login', methods=['POST'])
def login():
    """Login and retrieve user credentials"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401
        
    return jsonify({
        "message": "Login successful",
        "user_id": str(user.user_id),
        "role": user.role,
        "name": user.name,
        "email": user.email
    }), 200

# ============ PROFILE ROUTES ============

@api.route('/profile/<user_id>', methods=['GET', 'PUT'])
def profile(user_id):
    """Get or update user profile"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    if request.method == 'GET':
        result = {
            "user_id": str(user.user_id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "phone": user.phone,
            "location": user.location
        }
        if user.role == 'recruiter':
            result.update({
                "company": user.company,
                "job_title": user.job_title
            })
        return jsonify(result), 200
        
    elif request.method == 'PUT':
        data = request.get_json()
        user.name = data.get('name', user.name)
        user.phone = data.get('phone', user.phone)
        user.location = data.get('location', user.location)
        
        if user.role == 'recruiter':
            user.company = data.get('company', user.company)
            user.job_title = data.get('job_title', user.job_title)
            
        db.session.commit()
        return jsonify({"message": "Profile updated successfully"}), 200

# ============ JOB POSTING ROUTES ============

@api.route('/jobs', methods=['GET', 'POST'])
def jobs():
    """List all jobs or create a new job posting"""
    if request.method == 'POST':
        data = request.get_json()
        recruiter_id = data.get('recruiter_id')
        title = data.get('title')
        skills = data.get('skills', [])
        description = data.get('description', '')
        location = data.get('location', '')
        job_type = data.get('job_type', '')
        experience_level = data.get('experience_level', '')
        salary_min = data.get('salary_min')
        salary_max = data.get('salary_max')
        
        if not recruiter_id or not title:
            return jsonify({"error": "Missing recruiter_id or title"}), 400
        
        recruiter = Recruiter.query.get(recruiter_id)
        if not recruiter:
            return jsonify({"error": "Recruiter not found"}), 404
            
        new_job = Job(
            recruiter_id=recruiter_id,
            title=title,
            description=description,
            location=location,
            job_type=job_type,
            experience_level=experience_level,
            salary_min=float(salary_min) if salary_min else None,
            salary_max=float(salary_max) if salary_max else None
        )
        
        for skill_name in skills:
            if not skill_name.strip():
                continue
            skill = Skill.query.filter_by(skill_name=skill_name.lower()).first()
            if not skill:
                skill = Skill(skill_name=skill_name.lower())
                db.session.add(skill)
            if skill not in new_job.skills:
                new_job.skills.append(skill)
            
        db.session.add(new_job)
        db.session.commit()
        
        return jsonify({
            "message": "Job posted successfully",
            "job_id": str(new_job.job_id),
            "title": new_job.title,
            "skills": [s.skill_name for s in new_job.skills]
        }), 201
        
    elif request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        recruiter_id = request.args.get('recruiter_id')
        
        query = Job.query
        if recruiter_id:
            query = query.filter_by(recruiter_id=recruiter_id)
        
        pagination = query.order_by(Job.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        jobs_list = pagination.items
        
        result = {
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "pages": pagination.pages,
            "jobs": [format_job(job) for job in jobs_list]
        }
        
        return jsonify(result), 200

@api.route('/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get details of a specific job"""
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    return jsonify(format_job(job)), 200

# ============ RESUME & MATCHING ROUTES ============

@api.route('/resumes', methods=['POST', 'GET'])
def resumes():
    """Upload a new resume (text) or get applicant's resumes"""
    if request.method == 'POST':
        data = request.get_json()
        applicant_id = data.get('applicant_id')
        raw_text = data.get('raw_text', '')
        
        if not applicant_id:
            return jsonify({"error": "Missing applicant_id"}), 400
        
        applicant = Applicant.query.get(applicant_id)
        if not applicant:
            return jsonify({"error": "Applicant not found"}), 404
        
        extracted_skills = extract_skills_from_text(raw_text)
        
        new_resume = Resume(applicant_id=applicant_id, raw_text=raw_text)
        
        for skill_name in extracted_skills:
            skill = Skill.query.filter_by(skill_name=skill_name.lower()).first()
            if not skill:
                skill = Skill(skill_name=skill_name.lower())
                db.session.add(skill)
            if skill not in new_resume.skills:
                new_resume.skills.append(skill)
        
        db.session.add(new_resume)
        db.session.flush()
        
        create_rankings_for_resume(new_resume.resume_id, applicant_id)
        
        db.session.commit()
        
        return jsonify({
            "message": "Resume uploaded successfully",
            "resume_id": str(new_resume.resume_id),
            "skills_extracted": extracted_skills
        }), 201
    
    elif request.method == 'GET':
        applicant_id = request.args.get('applicant_id')
        if not applicant_id:
            return jsonify({"error": "Missing applicant_id"}), 400
        
        resumes_list = Resume.query.filter_by(applicant_id=applicant_id).order_by(Resume.uploaded_at.desc()).all()
        
        result = [{
            "resume_id": str(r.resume_id),
            "uploaded_at": r.uploaded_at.isoformat(),
            "file_path": r.file_path or "",
            "skills": [s.skill_name for s in r.skills]
        } for r in resumes_list]
        
        return jsonify(result), 200

@api.route('/resumes/upload-pdf', methods=['POST'])
def upload_resume_pdf():
    """Upload a PDF resume, extract text & skills, store in DB."""
    applicant_id = request.form.get('applicant_id')
    if not applicant_id:
        return jsonify({"error": "Missing applicant_id"}), 400
    
    applicant = Applicant.query.get(applicant_id)
    if not applicant:
        return jsonify({"error": "Applicant not found"}), 404
    
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({"error": "No file uploaded"}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are supported"}), 400
    
    try:
        file_bytes = file.read()
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        text = text.strip()
        
        if not text:
            return jsonify({"error": "The PDF has no readable text"}), 400
        
        extracted_skills = extract_skills_from_text(text)
        
        # Delete old resumes for this applicant (keep only the latest)
        old_resumes = Resume.query.filter_by(applicant_id=applicant_id).all()
        for old in old_resumes:
            db.session.delete(old)
        db.session.flush()
        
        new_resume = Resume(
            applicant_id=applicant_id,
            raw_text=text,
            file_path=file.filename
        )
        
        for skill_name in extracted_skills:
            skill = Skill.query.filter_by(skill_name=skill_name.lower()).first()
            if not skill:
                skill = Skill(skill_name=skill_name.lower())
                db.session.add(skill)
            if skill not in new_resume.skills:
                new_resume.skills.append(skill)
        
        db.session.add(new_resume)
        db.session.flush()
        
        create_rankings_for_resume(new_resume.resume_id, applicant_id)
        db.session.commit()
        
        return jsonify({
            "message": "Resume uploaded and analyzed successfully",
            "resume_id": str(new_resume.resume_id),
            "filename": file.filename,
            "uploaded_at": new_resume.uploaded_at.isoformat(),
            "skills_extracted": extracted_skills,
            "skill_count": len(extracted_skills)
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error parsing PDF: {str(e)}"}), 500

@api.route('/applicants/<applicant_id>/matched-jobs', methods=['GET'])
def get_matched_jobs(applicant_id):
    """Get all jobs matched to an applicant's resume with scores"""
    applicant = Applicant.query.get(applicant_id)
    if not applicant:
        return jsonify({"error": "Applicant not found"}), 404
    
    latest_resume = Resume.query.filter_by(applicant_id=applicant_id).order_by(Resume.uploaded_at.desc()).first()
    
    if not latest_resume:
        return jsonify({
            "total": 0,
            "page": 1,
            "per_page": 10,
            "pages": 0,
            "resume_id": None,
            "matched_jobs": []
        }), 200
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    min_score = request.args.get('min_score', 0, type=float)
    
    query = Ranking.query.filter(
        Ranking.resume_id == latest_resume.resume_id,
        Ranking.matching_score >= min_score
    ).order_by(Ranking.matching_score.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    rankings = pagination.items
    
    result = {
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages,
        "resume_id": str(latest_resume.resume_id),
        "matched_jobs": [{
            "job_id": str(r.job.job_id),
            "title": r.job.title,
            "recruiter_name": r.job.recruiter.name or "",
            "recruiter_company": r.job.recruiter.company or "",
            "location": r.job.location or "",
            "job_type": r.job.job_type or "",
            "salary_min": r.job.salary_min,
            "salary_max": r.job.salary_max,
            "matching_score": r.matching_score,
            "created_at": r.job.created_at.isoformat(),
            "skills": [s.skill_name for s in r.job.skills]
        } for r in rankings]
    }
    
    return jsonify(result), 200

@api.route('/applicants/<applicant_id>/dashboard', methods=['GET'])
def applicant_dashboard(applicant_id):
    """Get dashboard stats for an applicant"""
    applicant = Applicant.query.get(applicant_id)
    if not applicant:
        return jsonify({"error": "Applicant not found"}), 404
    
    latest_resume = Resume.query.filter_by(applicant_id=applicant_id).order_by(Resume.uploaded_at.desc()).first()
    
    # Compute average match score & top matched jobs
    avg_score = 0.0
    top_jobs = []
    skill_count = 0
    missing_skills = []
    
    if latest_resume:
        skill_count = len(latest_resume.skills)
        
        rankings = Ranking.query.filter_by(resume_id=latest_resume.resume_id)\
            .order_by(Ranking.matching_score.desc()).limit(10).all()
        
        if rankings:
            scores = [r.matching_score for r in rankings if r.matching_score]
            avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
            
            # Top 4 for display
            for r in rankings[:4]:
                top_jobs.append({
                    "job_id": str(r.job.job_id),
                    "title": r.job.title,
                    "recruiter_name": r.job.recruiter.name or "",
                    "recruiter_company": r.job.recruiter.company or "",
                    "location": r.job.location or "",
                    "matching_score": r.matching_score,
                    "skills": [s.skill_name for s in r.job.skills]
                })
            
            # Compute missing skills across top 4 jobs
            resume_skill_set = set(s.skill_name for s in latest_resume.skills)
            for r in rankings[:4]:
                job_skill_set = set(s.skill_name for s in r.job.skills)
                missing_skills.extend(job_skill_set - resume_skill_set)
            missing_skills = list(set(missing_skills))[:6]  # unique, max 6
    
    # Resume strength: based on skill count (0-100)
    resume_strength = min(int(skill_count * 10), 100)
    
    return jsonify({
        "name": applicant.name or applicant.email,
        "email": applicant.email,
        "has_resume": latest_resume is not None,
        "resume_uploaded_at": latest_resume.uploaded_at.isoformat() if latest_resume else None,
        "resume_filename": latest_resume.file_path if latest_resume else None,
        "skill_count": skill_count,
        "resume_strength": resume_strength,
        "avg_match_score": avg_score,
        "top_jobs": top_jobs,
        "missing_skills": missing_skills
    }), 200

@api.route('/applicants/<applicant_id>/skill-gap', methods=['GET'])
def applicant_skill_gap(applicant_id):
    """Compare applicant resume skills vs a specific job's skills"""
    applicant = Applicant.query.get(applicant_id)
    if not applicant:
        return jsonify({"error": "Applicant not found"}), 404
    
    job_id = request.args.get('job_id')
    
    latest_resume = Resume.query.filter_by(applicant_id=applicant_id).order_by(Resume.uploaded_at.desc()).first()
    if not latest_resume:
        return jsonify({"error": "No resume found. Please upload a resume first."}), 404
    
    resume_skill_set = set(s.skill_name for s in latest_resume.skills)
    
    if job_id:
        job = Job.query.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        job_skill_set = set(s.skill_name for s in job.skills)
        job_title = job.title
        job_company = job.recruiter.company or job.recruiter.name or ""
        
        matched = list(resume_skill_set.intersection(job_skill_set))
        missing = list(job_skill_set - resume_skill_set)
        
        total = len(job_skill_set)
        readiness = round((len(matched) / total * 100), 1) if total > 0 else 0.0
    else:
        # Aggregate across all ranked jobs
        all_rankings = Ranking.query.filter_by(resume_id=latest_resume.resume_id)\
            .order_by(Ranking.matching_score.desc()).limit(5).all()
        
        all_job_skills = set()
        for r in all_rankings:
            all_job_skills.update(s.skill_name for s in r.job.skills)
        
        matched = list(resume_skill_set.intersection(all_job_skills))
        missing = list(all_job_skills - resume_skill_set)
        total = len(all_job_skills)
        readiness = round((len(matched) / total * 100), 1) if total > 0 else 0.0
        job_title = "All Matched Jobs"
        job_company = ""
    
    # Priority heuristic: skills in many jobs = high priority
    missing_with_priority = []
    for skill in missing:
        missing_with_priority.append({
            "skill": skill,
            "priority": "High" if len(missing) <= 2 else ("Medium" if len(missing) <= 5 else "Low")
        })
    
    return jsonify({
        "job_id": job_id,
        "job_title": job_title,
        "job_company": job_company,
        "resume_skills": list(resume_skill_set),
        "matched_skills": matched,
        "missing_skills": missing_with_priority,
        "readiness_score": readiness
    }), 200

# ============ RECRUITER CANDIDATE ROUTES ============

@api.route('/jobs/<job_id>/candidates', methods=['GET'])
def get_job_candidates(job_id):
    """Get all candidates for a specific job, ranked by match score"""
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    min_score = request.args.get('min_score', 0, type=float)
    
    query = Ranking.query.filter(
        Ranking.job_id == job_id,
        Ranking.matching_score >= min_score
    ).order_by(Ranking.matching_score.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    rankings = pagination.items
    
    result = {
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages,
        "job_id": str(job_id),
        "job_title": job.title,
        "candidates": [{
            "ranking_id": str(r.ranking_id),
            "applicant_id": str(r.resume.applicant_id),
            "applicant_name": r.resume.applicant.name or r.resume.applicant.email,
            "applicant_email": r.resume.applicant.email,
            "applicant_location": r.resume.applicant.location or "",
            "matching_score": r.matching_score,
            "candidate_rank": r.candidate_rank,
            "resume_skills": [s.skill_name for s in r.resume.skills]
        } for r in rankings]
    }
    
    return jsonify(result), 200

@api.route('/recruiters/<recruiter_id>/candidates', methods=['GET'])
def get_recruiter_candidates(recruiter_id):
    """Get all candidates for all jobs posted by a recruiter"""
    recruiter = Recruiter.query.get(recruiter_id)
    if not recruiter:
        return jsonify({"error": "Recruiter not found"}), 404
    
    recruiter_jobs = Job.query.filter_by(recruiter_id=recruiter_id).all()
    job_ids = [job.job_id for job in recruiter_jobs]
    
    if not job_ids:
        return jsonify({
            "total": 0,
            "recruiter_id": str(recruiter_id),
            "candidates": [],
            "jobs": []
        }), 200
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    min_score = request.args.get('min_score', 0, type=float)
    job_filter = request.args.get('job_id')
    
    query = Ranking.query.filter(
        Ranking.job_id.in_(job_ids),
        Ranking.matching_score >= min_score
    )
    
    if job_filter and job_filter in [str(j) for j in job_ids]:
        query = query.filter(Ranking.job_id == job_filter)
    
    query = query.order_by(Ranking.matching_score.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    rankings = pagination.items
    
    result = {
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages,
        "recruiter_id": str(recruiter_id),
        "jobs": [{"job_id": str(j.job_id), "title": j.title} for j in recruiter_jobs],
        "candidates": [{
            "ranking_id": str(r.ranking_id),
            "job_id": str(r.job.job_id),
            "job_title": r.job.title,
            "applicant_id": str(r.resume.applicant_id),
            "applicant_name": r.resume.applicant.name or r.resume.applicant.email,
            "applicant_email": r.resume.applicant.email,
            "applicant_location": r.resume.applicant.location or "",
            "matching_score": r.matching_score,
            "candidate_rank": r.candidate_rank,
            "resume_skills": [s.skill_name for s in r.resume.skills]
        } for r in rankings]
    }
    
    return jsonify(result), 200

@api.route('/recruiters/<recruiter_id>/dashboard', methods=['GET'])
def recruiter_dashboard(recruiter_id):
    """Get dashboard stats for a recruiter"""
    recruiter = Recruiter.query.get(recruiter_id)
    if not recruiter:
        return jsonify({"error": "Recruiter not found"}), 404
    
    jobs = Job.query.filter_by(recruiter_id=recruiter_id).order_by(Job.created_at.desc()).all()
    job_ids = [j.job_id for j in jobs]
    
    total_candidates = 0
    top_candidates = []
    
    if job_ids:
        # Count unique applicants across all jobs
        total_candidates = db.session.query(func.count(func.distinct(Ranking.resume_id)))\
            .filter(Ranking.job_id.in_(job_ids)).scalar() or 0
        
        # Top 3 candidates by match score
        top_rankings = Ranking.query.filter(
            Ranking.job_id.in_(job_ids),
            Ranking.matching_score > 0
        ).order_by(Ranking.matching_score.desc()).limit(3).all()
        
        for r in top_rankings:
            top_candidates.append({
                "applicant_id": str(r.resume.applicant_id),
                "applicant_name": r.resume.applicant.name or r.resume.applicant.email,
                "applicant_email": r.resume.applicant.email,
                "applicant_location": r.resume.applicant.location or "",
                "job_title": r.job.title,
                "matching_score": r.matching_score,
                "resume_skills": [s.skill_name for s in r.resume.skills]
            })
    
    return jsonify({
        "name": recruiter.name or recruiter.email,
        "email": recruiter.email,
        "company": recruiter.company or "",
        "active_postings": len(jobs),
        "total_candidates": total_candidates,
        "jobs": [format_job(j) for j in jobs[:5]],  # show latest 5 in panel
        "top_candidates": top_candidates
    }), 200

@api.route('/recruiters/bulk-screen', methods=['POST'])
def bulk_screen():
    """
    Upload bulk resumes in PDF (max 50) and score/rank them against a job description.
    """
    uploaded_files = request.files.getlist('files')
    if not uploaded_files or len(uploaded_files) == 0 or (len(uploaded_files) == 1 and uploaded_files[0].filename == ''):
        return jsonify({"error": "No files uploaded"}), 400
        
    if len(uploaded_files) > 50:
        return jsonify({"error": "You can upload a maximum of 50 resumes"}), 400
        
    job_id = request.form.get('job_id')
    custom_title = request.form.get('custom_title', 'Custom Position')
    custom_skills_raw = request.form.get('custom_skills', '')
    custom_description = request.form.get('custom_description', '')
    
    job_skills_list = []
    job_title = custom_title
    job_desc = custom_description
    
    if job_id:
        job = Job.query.get(job_id)
        if not job:
            return jsonify({"error": "Selected job posting not found"}), 404
        job_skills_list = [s.skill_name.lower() for s in job.skills]
        job_title = job.title
        job_desc = f"{job.title} " + " ".join(job_skills_list)
    else:
        if custom_skills_raw:
            job_skills_list = [s.strip().lower() for s in custom_skills_raw.split(',') if s.strip()]
        
        if not job_skills_list and custom_description:
            job_skills_list = extract_skills_from_text(custom_description)
            
        if not job_desc:
            job_desc = f"{custom_title} " + " ".join(job_skills_list)

    if not job_skills_list and not job_desc:
        return jsonify({"error": "Please select a job or provide a job description/skills"}), 400

    results = []
    
    for file in uploaded_files:
        filename = file.filename
        if not filename.lower().endswith('.pdf'):
            results.append({
                "filename": filename,
                "candidate_name": filename,
                "match_score": 0.0,
                "error": "Only PDF files are supported"
            })
            continue
            
        try:
            file_bytes = file.read()
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            text = text.strip()
            
            if not text:
                results.append({
                    "filename": filename,
                    "candidate_name": filename,
                    "match_score": 0.0,
                    "error": "The PDF file has no readable text"
                })
                continue
                
            base_name, _ = os.path.splitext(filename)
            cleaned_name = base_name.replace('_', ' ').replace('-', ' ')
            words = cleaned_name.split()
            cleaned_words = [w for w in words if w.lower() not in ['resume', 'cv', 'final', 'pdf', 'job', 'application', '2026', '2025', '2024', 'updated']]
            candidate_name = " ".join(cleaned_words).title() if cleaned_words else cleaned_name.title()
            
            resume_skills = extract_skills_from_text(text)
            skills_score = calculate_match_score(resume_skills, job_skills_list)
            
            content_score = 0.0
            if job_desc and text:
                try:
                    vectorizer = TfidfVectorizer(stop_words='english')
                    tfidf = vectorizer.fit_transform([job_desc, text])
                    content_score = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]) * 100
                except Exception:
                    pass
            
            combined_score = (skills_score * 0.6) + (content_score * 0.4)
            combined_score = round(combined_score, 2)
            
            matched_skills = list(set(resume_skills).intersection(set(job_skills_list)))
            missing_skills = list(set(job_skills_list) - set(resume_skills))
            
            results.append({
                "filename": filename,
                "candidate_name": candidate_name,
                "match_score": combined_score,
                "skills_score": round(skills_score, 2),
                "content_score": round(content_score, 2),
                "extracted_skills": resume_skills,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "text_snippet": text[:250] + "..." if len(text) > 250 else text,
                "raw_text": text
            })
            
        except Exception as e:
            results.append({
                "filename": filename,
                "candidate_name": filename,
                "match_score": 0.0,
                "error": f"Error parsing PDF: {str(e)}"
            })
            
    results.sort(key=lambda x: x.get('match_score', 0), reverse=True)
    
    return jsonify({
        "job_title": job_title,
        "job_skills": job_skills_list,
        "total_screened": len(uploaded_files),
        "results": results
    }), 200

@api.route('/rankings/<ranking_id>', methods=['PUT'])
def update_ranking(ranking_id):
    """Update candidate ranking/status"""
    ranking = Ranking.query.get(ranking_id)
    if not ranking:
        return jsonify({"error": "Ranking not found"}), 404
    
    data = request.get_json()
    
    if 'candidate_rank' in data:
        ranking.candidate_rank = data.get('candidate_rank')
    
    db.session.commit()
    
    return jsonify({
        "message": "Ranking updated successfully",
        "ranking_id": str(ranking.ranking_id),
        "candidate_rank": ranking.candidate_rank
    }), 200
