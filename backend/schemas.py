"""Pydantic schemas for request/response validation."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, HttpUrl, validator

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
    name: str | None = None
    email: EmailStr
    email_verified: bool = False
    profile_image: str | None = None
    company: str | None = None
    job_title: str | None = None


class MeResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    name: str | None = None
    role: UserRole
    phone: str | None = None
    location: str | None = None
    profile_image: str | None = None
    email_verified: bool = False
    company: str | None = None
    job_title: str | None = None


# =============================================================================
# Profile Schemas
# =============================================================================

class ProfileUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    phone: str | None = Field(None, max_length=20)
    location: str | None = Field(None, max_length=255)

    @validator('name')
    def name_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v


class RecruiterProfileUpdateRequest(ProfileUpdateRequest):
    company: str | None = Field(None, max_length=255)
    job_title: str | None = Field(None, max_length=255)


class ProfileResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    name: str | None = None
    role: UserRole
    phone: str | None = None
    location: str | None = None
    profile_image: str | None = None
    email_verified: bool
    company: str | None = None
    job_title: str | None = None


# =============================================================================
# Job Schemas
# =============================================================================

class JobBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    location: str | None = Field(None, max_length=255)
    job_type: JobType | None = None
    experience_level: ExperienceLevel | None = None
    salary_min: float | None = Field(None, ge=0)
    salary_max: float | None = Field(None, ge=0)
    skills: list[str] = Field(default_factory=list)

    @validator('salary_max')
    def salary_max_gte_min(cls, v, values):
        if v is not None and 'salary_min' in values and values['salary_min'] is not None:
            if v < values['salary_min']:
                raise ValueError('salary_max must be >= salary_min')
        return v


class JobCreateRequest(JobBase):
    pass


class JobUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    location: str | None = Field(None, max_length=255)
    job_type: JobType | None = None
    experience_level: ExperienceLevel | None = None
    salary_min: float | None = Field(None, ge=0)
    salary_max: float | None = Field(None, ge=0)
    skills: list[str] | None = None


class JobSkill(BaseModel):
    skill_id: UUID
    skill_name: str


class JobResponse(JobBase):
    job_id: UUID
    recruiter_id: UUID
    recruiter_name: str | None = None
    recruiter_company: str | None = None
    recruiter_profile_image: str | None = None
    created_at: datetime
    skills: list[str] = []
    salary: str | None = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    jobs: list[JobResponse]


# =============================================================================
# Resume Schemas
# =============================================================================

class ResumeResponse(BaseModel):
    resume_id: UUID
    uploaded_at: datetime
    file_path: str
    file_url: str | None = None
    skills: list[str] = []
    skill_count: int

    class Config:
        from_attributes = True


class ResumeUploadResponse(BaseModel):
    message: str
    resume_id: UUID
    filename: str
    uploaded_at: datetime
    skills_extracted: list[str]
    skill_count: int
    file_url: str | None = None
    storage_provider: str | None = None


# =============================================================================
# Application Schemas
# =============================================================================

class JobApplicationResponse(BaseModel):
    application_id: UUID
    job_id: UUID
    applicant_id: UUID
    applied_at: datetime
    status: ApplicationStatus
    matching_score: float | None = None

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
    application_id: UUID | None = None


class MatchedJobsResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    resume_id: UUID
    matched_jobs: list[MatchedJobResponse]


class CandidatePreview(BaseModel):
    ranking_id: UUID
    job_id: UUID
    job_title: str
    applicant_id: UUID
    applicant_name: str
    applicant_email: str
    applicant_location: str
    matching_score: float
    resume_skills: list[str]


class CandidateListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    candidates: list[CandidatePreview]


# =============================================================================
# Skill Gap Schemas
# =============================================================================

class MissingSkill(BaseModel):
    skill_name: str
    priority: str  # high, medium, low
    matched_jobs_count: int


class SkillGapResponse(BaseModel):
    resume_id: UUID
    resume_skills: list[str]
    missing_skills: list[MissingSkill]
    readiness_score: float


# =============================================================================
# Interview Schemas
# =============================================================================

class InterviewCreateRequest(BaseModel):
    job_id: UUID
    applicant_id: UUID
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=15, le=480)
    notes: str | None = None
    meeting_link: HttpUrl | None = None


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
    notes: str | None = None
    meeting_link: str | None = None
    job_title: str | None = None
    applicant_name: str | None = None
    recruiter_name: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewListResponse(BaseModel):
    interviews: list[InterviewResponse]


# =============================================================================
# Notification Schemas
# =============================================================================

class NotificationResponse(BaseModel):
    notification_id: UUID
    title: str
    message: str
    type: NotificationType
    is_read: bool
    related_job_id: UUID | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]


# =============================================================================
# Bulk Screening Schemas
# =============================================================================

class BulkScreeningRequest(BaseModel):
    job_id: UUID | None = None
    custom_title: str | None = Field(None, max_length=255)
    custom_skills: list[str] | None = None
    custom_description: str | None = None


class BulkScreeningResult(BaseModel):
    filename: str
    matching_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    text_snippet: str


class BulkScreeningResponse(BaseModel):
    results: list[BulkScreeningResult]
    job_id: UUID | None = None
    custom_skills: list[str] = []


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
    model_score: float | None = None
    blended_score: float | None = None
    alpha: float | None = None
    heuristic: dict
    contributions: list[FeatureContribution]
    error: str | None = None


class ModelStatusResponse(BaseModel):
    available: bool
    model_version: str | None = None
    model_path: str | None = None
    trained_at: str | None = None
    row_count: int
    job_count: int
    alpha: float | None = None
    n_features: int | None = None
    metrics: dict
    min_training_rows: int


class TrainModelResponse(BaseModel):
    trained: bool
    message: str
    row_count: int = 0
    job_count: int = 0
    model_version: str | None = None
    model_path: str | None = None
    alpha: float | None = None
    n_features: int | None = None
    evaluation: str | None = None
    metrics: dict = {}


# =============================================================================
# Pagination & Filtering
# =============================================================================

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class JobFilterParams(PaginationParams):
    search: str | None = None
    job_type: JobType | None = None
    experience_level: ExperienceLevel | None = None
    location: str | None = None
    salary_min: float | None = Field(None, ge=0)
    salary_max: float | None = Field(None, ge=0)
    skill: str | None = None
    recruiter_id: UUID | None = None


class MatchedJobFilterParams(PaginationParams):
    min_score: float | None = Field(None, ge=0, le=100)
    search: str | None = None
    location: str | None = None
    job_type: JobType | None = None
    experience_level: ExperienceLevel | None = None
    salary_min: float | None = Field(None, ge=0)
    salary_max: float | None = Field(None, ge=0)
    skill: str | None = None


# =============================================================================
# Health Check
# =============================================================================

class HealthCheckResponse(BaseModel):
    status: str
    version: str
    checks: dict