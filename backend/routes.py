from flask import Blueprint, request, jsonify
from models import db, User, Applicant, Recruiter, Job, JobApplication, Resume, Skill, Ranking, Notification
from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import func
import fitz  # PyMuPDF
import os

from routes_common import (
    calculate_experience_score,
    calculate_match_score,
    calculate_ranking_score,
    create_rankings_for_job,
    create_rankings_for_resume,
    create_rankings_for_resume_after_delete,
    experience_level_to_years,
    extract_experience_years,
    extract_skills_from_text,
    format_candidate_preview,
    format_job,
)
from ranking_ml import get_ranking_model_status, train_ranking_model

api = Blueprint('api', __name__)

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
        
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long"}), 400
        
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
        
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long"}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401
        
    return jsonify({
        "message": "Login successful",
        "user_id": str(user.user_id),
        "role": user.role,
        "name": user.name,
        "email": user.email,
        "profile_image": user.profile_image
    }), 200


@api.route('/auth/logout', methods=['POST'])
def logout():
    """Clear any server-side auth state for the current client."""
    return jsonify({"message": "Logged out successfully"}), 200

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
            "location": user.location,
            "profile_image": user.profile_image
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
        if 'profile_image' in data:
            user.profile_image = data.get('profile_image')
        
        if user.role == 'recruiter':
            user.company = data.get('company', user.company)
            user.job_title = data.get('job_title', user.job_title)
            
        db.session.commit()
        return jsonify({"message": "Profile updated successfully"}), 200


@api.route('/public/preview', methods=['GET'])
def public_preview():
    """Return a public, database-backed snapshot for guests."""
    latest_jobs = Job.query.order_by(Job.created_at.desc()).limit(4).all()
    latest_rankings = Ranking.query.order_by(Ranking.matching_score.desc()).limit(4).all()

    total_jobs = Job.query.count()
    total_recruiters = Recruiter.query.count()
    total_applicants = Applicant.query.count()
    total_resumes = Resume.query.count()

    return jsonify({
        "stats": {
            "jobs": total_jobs,
            "recruiters": total_recruiters,
            "applicants": total_applicants,
            "resumes": total_resumes,
        },
        "recent_jobs": [format_job(job) for job in latest_jobs],
        "top_candidates": [format_candidate_preview(ranking) for ranking in latest_rankings],
    }), 200

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

        create_rankings_for_job(new_job.job_id)
        
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


@api.route('/jobs/<job_id>/apply', methods=['POST'])
def apply_for_job(job_id):
    """Record an applicant's interest in a job and create rankings only for applied candidates."""
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    data = request.get_json(silent=True) or {}
    applicant_id = data.get('applicant_id')
    if not applicant_id:
        return jsonify({"error": "Missing applicant_id"}), 400

    applicant = Applicant.query.get(applicant_id)
    if not applicant:
        return jsonify({"error": "Applicant not found"}), 404

    application = JobApplication.query.filter_by(job_id=job_id, applicant_id=applicant_id).first()
    created = False
    if not application:
        application = JobApplication(job_id=job_id, applicant_id=applicant_id)
        db.session.add(application)
        created = True
        
        # Create notification for applicant
        applicant_notif = Notification(
            user_id=applicant_id,
            title="Application Submitted",
            message=f"You have successfully applied for '{job.title}'.",
            type="success",
            related_job_id=job_id
        )
        db.session.add(applicant_notif)
        
        # Create notification for recruiter
        recruiter_notif = Notification(
            user_id=job.recruiter_id,
            title="New Job Application",
            message=f"{applicant.name} has applied for your job '{job.title}'.",
            type="info",
            related_job_id=job_id
        )
        db.session.add(recruiter_notif)
        
        db.session.flush()

    create_rankings_for_job(job_id)
    db.session.commit()

    latest_resume = Resume.query.filter_by(applicant_id=applicant_id).order_by(Resume.uploaded_at.desc()).first()

    return jsonify({
        "message": "Job application saved successfully" if created else "Job application already exists",
        "job_id": str(job.job_id),
        "applicant_id": str(applicant.user_id),
        "application_id": str(application.application_id),
        "has_resume": latest_resume is not None,
    }), 200 if not created else 201


@api.route('/applicants/<applicant_id>/applications', methods=['GET'])
def get_applicant_applications(applicant_id):
    """Get the job ids that an applicant has already applied to."""
    applicant = Applicant.query.get(applicant_id)
    if not applicant:
        return jsonify({"error": "Applicant not found"}), 404

    applications = JobApplication.query.filter_by(applicant_id=applicant_id).all()
    return jsonify({
        "applicant_id": str(applicant.user_id),
        "job_ids": [str(application.job_id) for application in applications],
    }), 200

@api.route('/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get details of a specific job"""
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    return jsonify(format_job(job)), 200

# ============ RESUME & MATCHING ROUTES ============

@api.route('/resumes/<resume_id>', methods=['GET', 'PUT', 'DELETE'])
def resume_detail(resume_id):
    """Fetch, update, or delete a single resume by id.

    PUT replaces the resume's raw_text and re-extracts its skill associations.
    It is the edit path for applicants who want to refine their profile after
    initial upload. DELETE removes the resume (cascade removes its rankings).
    """
    resume = Resume.query.get(resume_id)
    if not resume:
        return jsonify({"error": "Resume not found"}), 404

    if request.method == 'GET':
        return jsonify({
            "resume_id": str(resume.resume_id),
            "applicant_id": str(resume.applicant_id),
            "raw_text": resume.raw_text or "",
            "file_path": resume.file_path or "",
            "uploaded_at": resume.uploaded_at.isoformat() if resume.uploaded_at else None,
            "skills": [s.skill_name for s in resume.skills],
        }), 200

    if request.method == 'DELETE':
        applicant_id = str(resume.applicant_id)
        db.session.delete(resume)
        db.session.commit()
        # Refresh rankings for this applicant so any prior job applications
        # no longer surface a deleted resume.
        create_rankings_for_resume_after_delete(applicant_id)
        return jsonify({"message": "Resume deleted successfully"}), 200

    # PUT
    data = request.get_json(silent=True) or {}
    new_text = data.get('raw_text')
    new_file_path = data.get('file_path')
    # The client (builder) sends the edited skills list as the source of
    # truth. If it isn't provided, fall back to re-extracting from raw_text
    # (covers programmatic edits that don't go through the builder).
    client_skills = data.get('skills')

    if new_text is None or not isinstance(new_text, str):
        return jsonify({"error": "Missing or invalid 'raw_text'"}), 400

    resume.raw_text = new_text
    if new_file_path is not None:
        resume.file_path = new_file_path

    # Replace skill associations with a fresh extract so stale skills drop off.
    if isinstance(client_skills, list) and all(isinstance(s, str) for s in client_skills):
        extracted_skills = [s.strip().lower() for s in client_skills if s.strip()]
    else:
        extracted_skills = extract_skills_from_text(new_text)
    resume.skills.clear()
    db.session.flush()
    for skill_name in extracted_skills:
        skill = Skill.query.filter_by(skill_name=skill_name.lower()).first()
        if not skill:
            skill = Skill(skill_name=skill_name.lower())
            db.session.add(skill)
        if skill not in resume.skills:
            resume.skills.append(skill)

    db.session.flush()
    create_rankings_for_resume(resume.resume_id, str(resume.applicant_id))
    db.session.commit()

    return jsonify({
        "message": "Resume updated successfully",
        "resume_id": str(resume.resume_id),
        "skills_extracted": extracted_skills,
        "skill_count": len(extracted_skills),
    }), 200


@api.route('/resumes', methods=['POST', 'GET'])
def resumes():
    """Upload a new resume (text) or get applicant's resumes"""
    if request.method == 'POST':
        data = request.get_json()
        applicant_id = data.get('applicant_id')
        raw_text = data.get('raw_text', '')
        # The client (builder) sends the edited skills list as the source
        # of truth. If it isn't provided, fall back to re-extracting from
        # raw_text (covers programmatic edits that don't go through the
        # builder).
        client_skills = data.get('skills')

        if not applicant_id:
            return jsonify({"error": "Missing applicant_id"}), 400

        applicant = Applicant.query.get(applicant_id)
        if not applicant:
            return jsonify({"error": "Applicant not found"}), 404

        if isinstance(client_skills, list) and all(isinstance(s, str) for s in client_skills):
            extracted_skills = [s.strip().lower() for s in client_skills if s.strip()]
        else:
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

def _compute_job_match_score(resume, job):
    """Compute match score on the fly from a resume + job (skills + experience)."""
    if not resume or not job:
        return 0.0
    resume_skills = [s.skill_name for s in resume.skills]
    job_skills = [s.skill_name for s in job.skills]
    return calculate_ranking_score(resume, job)


@api.route('/applicants/<applicant_id>/matched-jobs', methods=['GET'])
def get_matched_jobs(applicant_id):
    """Return ALL job postings ranked by match score against the applicant's resume.

    Computes the match score on the fly so applicants can browse jobs even
    before they have applied to any. Each job also carries an ``applied`` flag
    indicating whether the applicant has already submitted an application.
    """
    applicant = Applicant.query.get(applicant_id)
    if not applicant:
        return jsonify({"error": "Applicant not found"}), 404

    latest_resume = (
        Resume.query.filter_by(applicant_id=applicant_id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )

    if not latest_resume:
        # No resume yet — return empty list but keep resume_id=None so the UI
        # can prompt the user to upload a resume.
        return jsonify({
            "total": 0,
            "page": 1,
            "per_page": 20,
            "pages": 0,
            "resume_id": None,
            "matched_jobs": []
        }), 200

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    min_score = request.args.get('min_score', 0, type=float)
    search = (request.args.get('search') or '').strip().lower()
    location = (request.args.get('location') or '').strip().lower()

    # Pull every job (lightweight list) and compute match score in Python so
    # we never miss a posting just because the applicant hasn't applied yet.
    all_jobs = Job.query.order_by(Job.created_at.desc()).all()
    applied_job_ids = {
        str(a.job_id)
        for a in JobApplication.query.filter_by(applicant_id=applicant_id).all()
    }

    enriched = []
    for job in all_jobs:
        score = _compute_job_match_score(latest_resume, job)
        if score < min_score:
            continue
        job_data = format_job(job)
        job_data["matching_score"] = round(float(score or 0.0), 2)
        job_data["applied"] = str(job.job_id) in applied_job_ids
        enriched.append(job_data)

    # Client-side search/location filters (cheap, in-memory).
    if search:
        enriched = [
            j for j in enriched
            if search in (j.get("title") or "").lower()
            or search in (j.get("recruiter_company") or "").lower()
            or search in (j.get("recruiter_name") or "").lower()
        ]
    if location and location != "all":
        enriched = [j for j in enriched if location in (j.get("location") or "").lower()]

    # Rank by match score (highest first); stable tiebreak by recency.
    enriched.sort(
        key=lambda j: (j.get("matching_score", 0.0), j.get("created_at") or ""),
        reverse=True,
    )

    total = len(enriched)
    pages = max(1, (total + per_page - 1) // per_page) if total else 0
    start = (page - 1) * per_page
    page_items = enriched[start:start + per_page]

    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
        "resume_id": str(latest_resume.resume_id),
        "matched_jobs": page_items,
    }), 200

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
    recent_jobs = [format_job(job) for job in Job.query.order_by(Job.created_at.desc()).limit(6).all()]
    skill_count = 0
    missing_skills = []
    
    if latest_resume:
        skill_count = len(latest_resume.skills)

        # Score every job on the fly so the dashboard surfaces jobs the
        # applicant could apply to (not just ones they already applied for).
        all_jobs_for_scoring = Job.query.order_by(Job.created_at.desc()).all()
        scored_jobs = []
        for job in all_jobs_for_scoring:
            score = _compute_job_match_score(latest_resume, job)
            scored_jobs.append((score, job))
        scored_jobs.sort(key=lambda pair: pair[0], reverse=True)

        top4 = scored_jobs[:4]
        if top4:
            scores = [s for s, _ in top4 if s]
            avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

            for score, job in top4:
                top_jobs.append({
                    "job_id": str(job.job_id),
                    "title": job.title,
                    "recruiter_name": job.recruiter.name or "",
                    "recruiter_company": job.recruiter.company or "",
                    "location": job.location or "",
                    "matching_score": round(float(score or 0.0), 2),
                    "skills": [s.skill_name for s in job.skills]
                })

            # Compute missing skills across the top matches
            resume_skill_set = set(s.skill_name for s in latest_resume.skills)
            for _, job in top4:
                job_skill_set = set(s.skill_name for s in job.skills)
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
        "recent_jobs": recent_jobs,
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


@api.route('/ml/ranking/status', methods=['GET'])
def ranking_model_status():
    """Report whether the trained ranking model is available and what it scored."""
    return jsonify(get_ranking_model_status()), 200


@api.route('/ml/ranking/train', methods=['POST'])
def ranking_model_train():
    """Train the ranking model from stored resume/job pairs and report evaluation metrics."""
    result = train_ranking_model()
    status_code = 200 if result.get("trained") else 400
    return jsonify(result), status_code

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
    
    # An applicant can only appear in a job's candidate list if they applied
    # to that specific job. The join+filter pair enforces this on both axes:
    #   - JobApplication.applicant_id must equal the resume's applicant
    #   - JobApplication.job_id must equal the ranking's job_id
    query = Ranking.query.join(Resume).join(
        JobApplication,
        (JobApplication.applicant_id == Resume.applicant_id)
        & (JobApplication.job_id == Ranking.job_id),
    ).filter(
        Ranking.job_id == job_id,
        Ranking.matching_score >= min_score,
    ).order_by(Ranking.matching_score.desc())

    # Deduplicate by ranking_id: a resume re-uploaded via the text /resumes
    # path keeps the prior rows in the DB until the cleanup pass prunes them.
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    seen: set[str] = set()
    rankings: list = []
    for r in pagination.items:
        if str(r.ranking_id) in seen:
            continue
        seen.add(str(r.ranking_id))
        rankings.append(r)
    
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
    
    # Pair the ranking with the application for the SAME job, so an applicant
    # can only appear in the candidate list of jobs they actually applied to.
    query = Ranking.query.join(Resume).join(
        JobApplication,
        (JobApplication.applicant_id == Resume.applicant_id)
        & (JobApplication.job_id == Ranking.job_id),
    ).filter(
        Ranking.job_id.in_(job_ids),
        Ranking.matching_score >= min_score,
    )

    if job_filter and job_filter in [str(j) for j in job_ids]:
        query = query.filter(Ranking.job_id == job_filter)

    query = query.order_by(Ranking.matching_score.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    seen: set[str] = set()
    rankings: list = []
    for r in pagination.items:
        if str(r.ranking_id) in seen:
            continue
        seen.add(str(r.ranking_id))
        rankings.append(r)
    
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
            "applicant_profile_image": r.resume.applicant.profile_image,
            "matching_score": r.matching_score,
            "candidate_rank": r.candidate_rank,
            "resume_skills": [s.skill_name for s in r.resume.skills],
            "application_id": str(app.application_id) if (app := JobApplication.query.filter_by(
                job_id=r.job.job_id, applicant_id=r.resume.applicant_id).first()) else None,
            "application_status": app.status if app else "pending",
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
        # Count unique applicants across all jobs. An applicant only counts
        # for a job if they applied to that specific job.
        total_candidates = db.session.query(func.count(func.distinct(Ranking.resume_id)))\
            .join(Resume, Resume.resume_id == Ranking.resume_id)\
            .join(
                JobApplication,
                (JobApplication.applicant_id == Resume.applicant_id)
                & (JobApplication.job_id == Ranking.job_id),
            )\
            .filter(Ranking.job_id.in_(job_ids)).scalar() or 0

        # Top 3 candidates by match score (deduplicated by ranking_id).
        top_query = Ranking.query.join(Resume).join(
            JobApplication,
            (JobApplication.applicant_id == Resume.applicant_id)
            & (JobApplication.job_id == Ranking.job_id),
        ).filter(
            Ranking.job_id.in_(job_ids),
            Ranking.matching_score > 0
        ).order_by(Ranking.matching_score.desc())

        seen: set[str] = set()
        for r in top_query.all():
            if str(r.ranking_id) in seen:
                continue
            seen.add(str(r.ranking_id))
            top_candidates.append({
                "applicant_id": str(r.resume.applicant_id),
                "applicant_name": r.resume.applicant.name or r.resume.applicant.email,
                "applicant_email": r.resume.applicant.email,
                "applicant_location": r.resume.applicant.location or "",
                "job_title": r.job.title,
                "matching_score": r.matching_score,
                "resume_skills": [s.skill_name for s in r.resume.skills]
            })
            if len(top_candidates) >= 3:
                break
    
    return jsonify({
        "name": recruiter.name or recruiter.email,
        "email": recruiter.email,
        "company": recruiter.company or "",
        "active_postings": len(jobs),
        "total_candidates": total_candidates,
        "top_match_score": top_candidates[0]["matching_score"] if top_candidates else 0,
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
    target_experience_years = None
    
    if job_id:
        job = Job.query.get(job_id)
        if not job:
            return jsonify({"error": "Selected job posting not found"}), 404
        job_skills_list = [s.skill_name.lower() for s in job.skills]
        job_title = job.title
        job_desc = f"{job.title} " + " ".join(job_skills_list)
        target_experience_years = experience_level_to_years(job.experience_level)
    else:
        if custom_skills_raw:
            job_skills_list = [s.strip().lower() for s in custom_skills_raw.split(',') if s.strip()]
        
        if not job_skills_list and custom_description:
            job_skills_list = extract_skills_from_text(custom_description)
            
        if not job_desc:
            job_desc = f"{custom_title} " + " ".join(job_skills_list)
        target_experience_years = extract_experience_years(custom_description)

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
            experience_years = extract_experience_years(text)
            experience_score = calculate_experience_score(experience_years, target_experience_years)
            
            content_score = 0.0
            if job_desc and text:
                try:
                    vectorizer = TfidfVectorizer(stop_words='english')
                    tfidf = vectorizer.fit_transform([job_desc, text])
                    content_score = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]) * 100
                except Exception:
                    pass
            
            if skills_score == 100.0 and experience_score >= 100.0:
                combined_score = 100.0
            else:
                combined_score = (skills_score * 0.88) + (experience_score * 0.10) + (content_score * 0.02)
                combined_score = min(round(combined_score, 2), 99.99)
            
            matched_skills = list(set(resume_skills).intersection(set(job_skills_list)))
            missing_skills = list(set(job_skills_list) - set(resume_skills))
            
            results.append({
                "filename": filename,
                "candidate_name": candidate_name,
                "match_score": combined_score,
                "skills_score": round(skills_score, 2),
                "experience_years": experience_years,
                "experience_score": round(experience_score, 2),
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
            
    results.sort(
        key=lambda x: (
            x.get('skills_score', 0),
            x.get('experience_years') if x.get('experience_years') is not None else -1,
            x.get('experience_score', 0),
            x.get('content_score', 0),
            x.get('match_score', 0),
        ),
        reverse=True,
    )
    
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


# ============ NOTIFICATION ROUTES ============

@api.route('/notifications/<user_id>', methods=['GET'])
def get_notifications(user_id):
    """Get notifications for a user"""
    notifications = Notification.query.filter_by(user_id=user_id).order_by(
        Notification.created_at.desc()
    ).limit(50).all()
    return jsonify([{
        "notification_id": str(n.notification_id),
        "title": n.title,
        "message": n.message,
        "type": n.type,
        "is_read": n.is_read,
        "related_job_id": str(n.related_job_id) if n.related_job_id else None,
        "related_job_title": n.related_job.title if n.related_job else None,
        "created_at": n.created_at.isoformat(),
    } for n in notifications]), 200


@api.route('/notifications/<notification_id>/read', methods=['PATCH'])
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    n = Notification.query.get(notification_id)
    if not n:
        return jsonify({"error": "Not found"}), 404
    n.is_read = True
    db.session.commit()
    return jsonify({"success": True}), 200


@api.route('/notifications/read-all/<user_id>', methods=['PATCH'])
def mark_all_notifications_read(user_id):
    """Mark all notifications as read for a user"""
    Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"success": True}), 200


# ============ APPLICATION STATUS / SHORTLIST ROUTES ============

@api.route('/applications/<application_id>/status', methods=['PATCH'])
def update_application_status(application_id):
    """Update status of a job application (shortlist / reject / pending)"""
    application = JobApplication.query.get(application_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404

    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ('pending', 'shortlisted', 'rejected'):
        return jsonify({"error": "Invalid status. Must be pending, shortlisted, or rejected."}), 400

    old_status = application.status
    application.status = new_status

    # Create notification for the applicant if status changed
    if new_status != old_status:
        job = Job.query.get(application.job_id)
        job_title = job.title if job else "a position"
        recruiter = Recruiter.query.get(job.recruiter_id) if job else None
        company = getattr(recruiter, 'company', None) or (recruiter.name if recruiter else None) or "the recruiter"

        if new_status == 'shortlisted':
            notif = Notification(
                user_id=application.applicant_id,
                title="🎉 You've been shortlisted!",
                message=f"Congratulations! You have been shortlisted for {job_title} by {company}.",
                type='shortlisted',
                related_job_id=application.job_id,
            )
        elif new_status == 'rejected':
            notif = Notification(
                user_id=application.applicant_id,
                title="Application Update",
                message=f"Your application for {job_title} was not selected at this time. Keep applying!",
                type='rejected',
                related_job_id=application.job_id,
            )
        else:
            notif = Notification(
                user_id=application.applicant_id,
                title="Application Status Update",
                message=f"Your application for {job_title} status changed to: {new_status}.",
                type='info',
                related_job_id=application.job_id,
            )
        db.session.add(notif)

    db.session.commit()
    return jsonify({
        "success": True,
        "application_id": str(application.application_id),
        "status": application.status,
    }), 200


@api.route('/jobs/<job_id>/application-status/<applicant_id>', methods=['GET'])
def get_application_status(job_id, applicant_id):
    """Get the status and application_id for a specific application"""
    application = JobApplication.query.filter_by(
        job_id=job_id, applicant_id=applicant_id
    ).first()
    if not application:
        return jsonify({"error": "Application not found"}), 404
    return jsonify({
        "application_id": str(application.application_id),
        "status": application.status,
    }), 200
