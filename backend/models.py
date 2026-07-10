from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

db = SQLAlchemy()

# Junction tables
job_skills = db.Table('job_skills',
    db.Column('job_id', UUID(as_uuid=True), db.ForeignKey('jobs.job_id', ondelete='CASCADE'), primary_key=True),
    db.Column('skill_id', UUID(as_uuid=True), db.ForeignKey('skills.skill_id', ondelete='CASCADE'), primary_key=True)
)

resume_skills = db.Table('resume_skills',
    db.Column('resume_id', UUID(as_uuid=True), db.ForeignKey('resumes.resume_id', ondelete='CASCADE'), primary_key=True),
    db.Column('skill_id', UUID(as_uuid=True), db.ForeignKey('skills.skill_id', ondelete='CASCADE'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=True) # Added name field
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'applicant' or 'recruiter'
    phone = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    
    __mapper_args__ = {
        'polymorphic_on': role,
        'polymorphic_identity': 'user'
    }

class Applicant(User):
    __tablename__ = 'applicants'
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    resumes = db.relationship('Resume', backref='applicant', lazy=True, cascade='all, delete-orphan')

    __mapper_args__ = {
        'polymorphic_identity': 'applicant',
    }

class Recruiter(User):
    __tablename__ = 'recruiters'
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    company = db.Column(db.String(255), nullable=True)
    job_title = db.Column(db.String(255), nullable=True)
    jobs = db.relationship('Job', backref='recruiter', lazy=True, cascade='all, delete-orphan')

    __mapper_args__ = {
        'polymorphic_identity': 'recruiter',
    }

class Skill(db.Model):
    __tablename__ = 'skills'
    skill_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_name = db.Column(db.String(100), unique=True, nullable=False)

class Job(db.Model):
    __tablename__ = 'jobs'
    job_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id = db.Column(UUID(as_uuid=True), db.ForeignKey('recruiters.user_id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    job_type = db.Column(db.String(50), nullable=True)  # full-time, part-time, contract
    experience_level = db.Column(db.String(50), nullable=True)  # fresher, 1-3, 3-5, 5+
    salary_min = db.Column(db.Float, nullable=True)
    salary_max = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    skills = db.relationship('Skill', secondary=job_skills, backref=db.backref('jobs', lazy='dynamic'))
    rankings = db.relationship('Ranking', backref='job', lazy=True, cascade='all, delete-orphan')
    applications = db.relationship('JobApplication', backref='job', lazy=True, cascade='all, delete-orphan')

class Resume(db.Model):
    __tablename__ = 'resumes'
    resume_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('applicants.user_id', ondelete='CASCADE'), nullable=False)
    raw_text = db.Column(db.Text)
    file_path = db.Column(db.String(500))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    skills = db.relationship('Skill', secondary=resume_skills, backref=db.backref('resumes', lazy='dynamic'))
    rankings = db.relationship('Ranking', backref='resume', lazy=True, cascade='all, delete-orphan')


class JobApplication(db.Model):
    __tablename__ = 'job_applications'
    application_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = db.Column(UUID(as_uuid=True), db.ForeignKey('jobs.job_id', ondelete='CASCADE'), nullable=False)
    applicant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('applicants.user_id', ondelete='CASCADE'), nullable=False)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('job_id', 'applicant_id', name='uq_job_applicant_application'),
    )

    applicant = db.relationship('Applicant', backref='job_applications')

class Ranking(db.Model):
    __tablename__ = 'rankings'
    ranking_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = db.Column(UUID(as_uuid=True), db.ForeignKey('jobs.job_id', ondelete='CASCADE'), nullable=False)
    resume_id = db.Column(UUID(as_uuid=True), db.ForeignKey('resumes.resume_id', ondelete='CASCADE'), nullable=False)
    matching_score = db.Column(db.Float)
    candidate_rank = db.Column(db.Integer)
