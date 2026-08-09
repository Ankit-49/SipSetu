"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator, HttpUrl
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class UserRole(str, Enum):
    applicant = "applicant"
    recruiter = "recruiter"


class JobType(str, Enum):
    full_time = "full-time"
    part_time = "part-time"
    contract = "contract"
    internship = "internship"


class ExperienceLevel(str, Enum):
    fresher = "fresher"
    one_to_three = "1-3"
    three_to_five = "3-5"
    five_plus = "5+"


class ApplicationStatus(str, Enum):
    pending = "pending"
    shortlisted = "shortlisted"
    rejected = "rejected"


class InterviewStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"
    declined = "declined"


class NotificationType(str, Enum):
    info = "info"
    success = "success"
    warning = "warning"
    shortlisted = "shortlisted"
    rejected = "rejected"


# =============================================================================
# Auth Schemas
# =============================================================================

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole

    @validator('name')
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')


class ResetPasswordRequest(BaseModel):
    token: str
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')


class ResendVerificationRequest(BaseModel):
    pass  # Uses auth from token


class AuthResponse(BaseModel):
    message: str
    token: str
    user_id: UUID
    role: UserRole
    name: Optional[str] = None
    email: EmailStr
    email_verified: bool = False
    profile_image: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None


class MeResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    name: Optional[str] = None
    role: UserRole
    phone: Optional[str] = None
    location: Optional[str] = None
    profile_image: Optional[str] = None
    email_verified: bool = False
    company: Optional[str] = None
    job_title: Optional[str] = None


# =============================================================================
# Profile Schemas
# =============================================================================

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=255)

    @validator('name')
    def name_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v


class RecruiterProfileUpdateRequest(ProfileUpdateRequest):
    company: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)


class ProfileResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    name: Optional[str] = None
    role: UserRole
    phone: Optional[str] = None
    location: Optional[str] = None
    profile_image: Optional[str] = None
    email_verified: bool
    company: Optional[str] = None
    job_title: Optional[str] = None


# =============================================================================
# Job Schemas
# =============================================================================

class JobBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    job_type: Optional[JobType] = None
    experience_level: Optional[ExperienceLevel] = None
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)
    skills: List[str] = Field(default_factory=list)

    @validator('salary_max')
    def salary_max_gte_min(cls, v, values):
        if v is not None and 'salary_min' in values and values['salary_min'] is not None:
            if v < values['salary_min']:
                raise ValueError('salary_max must be >= salary_min')
        return v


class JobCreateRequest(JobBase):
    pass


class JobUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    job_type: Optional[JobType] = None
    experience_level: Optional[ExperienceLevel] = None
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)
    skills: Optional[List[str]] = None


class JobSkill(BaseModel):
    skill_id: UUID
    skill_name: str


class JobResponse(JobBase):
    job_id: UUID
    recruiter_id: UUID
    recruiter_name: Optional[str] = None
    recruiter_company: Optional[str] = None
    recruiter_profile_image: Optional[str] = None
    created_at: datetime
    skills: List[str] = []
    salary: Optional[str] = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    jobs: List[JobResponse]


# =============================================================================
# Resume Schemas
# =============================================================================

class ResumeResponse(BaseModel):
    resume_id: UUID
    uploaded_at: datetime
    file_path: str
    file_url: Optional[str] = None
    skills: List[str] = []
    skill_count: int

    class Config:
        from_attributes = True


class ResumeUploadResponse(BaseModel):
    message: str
    resume_id: UUID
    filename: str
    uploaded_at: datetime
    skills_extracted: List[str]
    skill_count: int
    file_url: Optional[str] = None
    storage_provider: Optional[str] = None


# =============================================================================
# Application Schemas
# =============================================================================

class JobApplicationResponse(BaseModel):
    application_id: UUID
    job_id: UUID
    applicant_id: UUID
    applied_at: datetime
    status: ApplicationStatus
    matching_score: Optional[float] = None

    class Config:
        from_attributes = True


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


# =============================================================================
# Ranking Schemas
# =============================================================================

class MatchedJobResponse(JobResponse):
    matching_score: float
    applied: bool
    application_id: Optional[UUID] = None


class MatchedJobsResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    resume_id: UUID
    matched_jobs: List[MatchedJobResponse]


class CandidatePreview(BaseModel):
    ranking_id: UUID
    job_id: UUID
    job_title: str
    applicant_id: UUID
    applicant_name: str
    applicant_email: str
    applicant_location: str
    matching_score: float
    resume_skills: List[str]


class CandidateListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    candidates: List[CandidatePreview]


# =============================================================================
# Skill Gap Schemas
# =============================================================================

class MissingSkill(BaseModel):
    skill_name: str
    priority: str  # high, medium, low
    matched_jobs_count: int


class SkillGapResponse(BaseModel):
    resume_id: UUID
    resume_skills: List[str]
    missing_skills: List[MissingSkill]
    readiness_score: float


# =============================================================================
# Interview Schemas
# =============================================================================

class InterviewCreateRequest(BaseModel):
    job_id: UUID
    applicant_id: UUID
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=15, le=480)
    notes: Optional[str] = None
    meeting_link: Optional[HttpUrl] = None


class InterviewStatusUpdate(BaseModel):
    status: InterviewStatus


class InterviewResponse(BaseModel):
    interview_id: UUID
    job_id: UUID
    applicant_id: UUID
    recruiter_id: UUID
    scheduled_at: datetime
    duration_minutes: int
    status: InterviewStatus
    notes: Optional[str] = None
    meeting_link: Optional[str] = None
    job_title: Optional[str] = None
    applicant_name: Optional[str] = None
    recruiter_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewListResponse(BaseModel):
    interviews: List[InterviewResponse]


# =============================================================================
# Notification Schemas
# =============================================================================

class NotificationResponse(BaseModel):
    notification_id: UUID
    title: str
    message: str
    type: NotificationType
    is_read: bool
    related_job_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]


# =============================================================================
# Bulk Screening Schemas
# =============================================================================

class BulkScreeningRequest(BaseModel):
    job_id: Optional[UUID] = None
    custom_title: Optional[str] = Field(None, max_length=255)
    custom_skills: Optional[List[str]] = None
    custom_description: Optional[str] = None


class BulkScreeningResult(BaseModel):
    filename: str
    matching_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    text_snippet: str


class BulkScreeningResponse(BaseModel):
    results: List[BulkScreeningResult]
    job_id: Optional[UUID] = None
    custom_skills: List[str] = []


# =============================================================================
# ML Ranking Schemas
# =============================================================================

class FeatureContribution(BaseModel):
    feature: str
    label: str
    description: str
    value: float
    baseline: float
    contribution: float
    direction: str  # up, down, neutral


class RankingExplanationResponse(BaseModel):
    available: bool
    model_score: Optional[float] = None
    blended_score: Optional[float] = None
    alpha: Optional[float] = None
    heuristic: dict
    contributions: List[FeatureContribution]
    error: Optional[str] = None


class ModelStatusResponse(BaseModel):
    available: bool
    model_version: Optional[str] = None
    model_path: Optional[str] = None
    trained_at: Optional[str] = None
    row_count: int
    job_count: int
    alpha: Optional[float] = None
    n_features: Optional[int] = None
    metrics: dict
    min_training_rows: int


class TrainModelResponse(BaseModel):
    trained: bool
    message: str
    row_count: int = 0
    job_count: int = 0
    model_version: Optional[str] = None
    model_path: Optional[str] = None
    alpha: Optional[float] = None
    n_features: Optional[int] = None
    evaluation: Optional[str] = None
    metrics: dict = {}


# =============================================================================
# Pagination & Filtering
# =============================================================================

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class JobFilterParams(PaginationParams):
    search: Optional[str] = None
    job_type: Optional[JobType] = None
    experience_level: Optional[ExperienceLevel] = None
    location: Optional[str] = None
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)
    skill: Optional[str] = None
    recruiter_id: Optional[UUID] = None


class MatchedJobFilterParams(PaginationParams):
    min_score: Optional[float] = Field(None, ge=0, le=100)
    search: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[JobType] = None
    experience_level: Optional[ExperienceLevel] = None
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)
    skill: Optional[str] = None


# =============================================================================
# Health Check
# =============================================================================

class HealthCheckResponse(BaseModel):
    status: str
    version: str
    checks: dict