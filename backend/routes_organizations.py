"""Organization & team management routes (Phase 6.1).

Provides CRUD for organizations, member invitation/role management,
organization-scoped job filtering, and team dashboard statistics.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from flask import Blueprint, g, jsonify, request
from sqlalchemy import func

from auth_middleware import require_auth
from models import (
    AuditLog,
    Job,
    JobApplication,
    Organization,
    OrganizationMember,
    Ranking,
    Recruiter,
    Resume,
    User,
    db,
)
from routes_common import format_job

orgs_bp = Blueprint('orgs', __name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ORG_ROLES = {'owner', 'admin', 'hiring_manager', 'interviewer', 'viewer'}
ADMIN_ORG_ROLES = {'owner', 'admin'}


def _get_org_or_404(org_id: str):
    org = Organization.query.get(org_id)
    if not org:
        return None, (jsonify({"error": "Organization not found"}), 404)
    return org, None


def _get_membership(org_id: str, user_id: str):
    return OrganizationMember.query.filter_by(org_id=org_id, user_id=user_id).first()


def _require_org_admin(org_id: str):
    """Return (org, error_response) — error_response is None if user is admin/owner."""
    org, err = _get_org_or_404(org_id)
    if err:
        return None, err
    membership = _get_membership(org_id, g.current_user_id)
    if not membership or membership.role not in ADMIN_ORG_ROLES:
        return None, (jsonify({"error": "Organization admin access required"}), 403)
    return org, None


def _format_org(org: Organization) -> dict:
    return {
        "org_id": str(org.org_id),
        "name": org.name,
        "slug": org.slug,
        "logo_url": org.logo_url,
        "description": org.description,
        "website": org.website,
        "industry": org.industry,
        "size": org.size,
        "created_at": org.created_at.isoformat() if org.created_at else None,
        "member_count": len(org.members),
    }


def _format_member(membership: OrganizationMember) -> dict:
    user = User.query.get(membership.user_id)
    inviter = User.query.get(membership.invited_by) if membership.invited_by else None
    return {
        "membership_id": str(membership.membership_id),
        "user_id": str(membership.user_id),
        "email": user.email if user else None,
        "name": user.name if user else None,
        "role": membership.role,
        "invited_by": str(membership.invited_by) if membership.invited_by else None,
        "inviter_name": inviter.name if inviter else None,
        "joined_at": membership.joined_at.isoformat() if membership.joined_at else None,
    }


def _log_org_audit(actor_id, action, org_id, details=None):
    db.session.add(AuditLog(
        actor_id=actor_id,
        action=action,
        target_type='organization',
        target_id=str(org_id),
        details=json.dumps(details) if details else None,
    ))


# ---------------------------------------------------------------------------
# Organization CRUD
# ---------------------------------------------------------------------------

@orgs_bp.route('/organizations', methods=['POST'])
@require_auth
def create_organization():
    """Create a new organization. The creator becomes the owner."""
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    slug = (data.get('slug') or '').strip().lower().replace(' ', '-')

    if not name:
        return jsonify({"error": "Organization name is required"}), 400
    if not slug or len(slug) < 2:
        return jsonify({"error": "Slug must be at least 2 characters"}), 400

    # Only recruiters can create organizations
    user = User.query.get(g.current_user_id)
    if not user or user.role != 'recruiter':
        return jsonify({"error": "Only recruiters can create organizations"}), 403

    if Organization.query.filter_by(slug=slug).first():
        return jsonify({"error": "An organization with this slug already exists"}), 409

    org = Organization(
        name=name,
        slug=slug,
        logo_url=data.get('logo_url'),
        description=data.get('description'),
        website=data.get('website'),
        industry=data.get('industry'),
        size=data.get('size'),
    )
    db.session.add(org)
    db.session.flush()

    # Creator becomes owner
    membership = OrganizationMember(
        org_id=org.org_id,
        user_id=g.current_user_id,
        role='owner',
        invited_by=g.current_user_id,
    )
    db.session.add(membership)
    _log_org_audit(g.current_user_id, 'org_created', org.org_id, {"name": name})
    db.session.commit()

    return jsonify({
        "message": "Organization created successfully",
        **_format_org(org),
    }), 201


@orgs_bp.route('/organizations', methods=['GET'])
@require_auth
def list_organizations():
    """List organizations the current user belongs to."""
    memberships = OrganizationMember.query.filter_by(user_id=g.current_user_id).all()
    org_ids = [m.org_id for m in memberships]
    orgs = Organization.query.filter(Organization.org_id.in_(org_ids)).all() if org_ids else []
    return jsonify({
        "organizations": [_format_org(o) for o in orgs],
        "total": len(orgs),
    }), 200


@orgs_bp.route('/organizations/<org_id>', methods=['GET'])
@require_auth
def get_organization(org_id):
    """Get organization details. User must be a member."""
    org, err = _get_org_or_404(org_id)
    if err:
        return err
    membership = _get_membership(org_id, g.current_user_id)
    if not membership:
        return jsonify({"error": "You are not a member of this organization"}), 403
    result = _format_org(org)
    result["your_role"] = membership.role
    return jsonify(result), 200


@orgs_bp.route('/organizations/<org_id>', methods=['PUT'])
@require_auth
def update_organization(org_id):
    """Update organization details (owner/admin only)."""
    org, err = _require_org_admin(org_id)
    if err:
        return err
    data = request.get_json() or {}

    for field in ('name', 'description', 'website', 'industry', 'size', 'logo_url'):
        if field in data:
            setattr(org, field, data[field])

    _log_org_audit(g.current_user_id, 'org_updated', org.org_id, data)
    db.session.commit()

    return jsonify({"message": "Organization updated", **_format_org(org)}), 200


@orgs_bp.route('/organizations/<org_id>', methods=['DELETE'])
@require_auth
def delete_organization(org_id):
    """Delete an organization (owner only)."""
    org = Organization.query.get(org_id)
    if not org:
        return jsonify({"error": "Organization not found"}), 404
    membership = _get_membership(org_id, g.current_user_id)
    if not membership or membership.role != 'owner':
        return jsonify({"error": "Only the owner can delete an organization"}), 403

    _log_org_audit(g.current_user_id, 'org_deleted', org.org_id)
    # Nullify org_id on all jobs before deletion
    Job.query.filter_by(organization_id=org.org_id).update({"organization_id": None})
    db.session.delete(org)
    db.session.commit()
    return jsonify({"message": "Organization deleted"}), 200


# ---------------------------------------------------------------------------
# Member management
# ---------------------------------------------------------------------------

@orgs_bp.route('/organizations/<org_id>/members', methods=['GET'])
@require_auth
def list_members(org_id):
    """List all members of an organization."""
    _org, err = _get_org_or_404(org_id)
    if err:
        return err
    membership = _get_membership(org_id, g.current_user_id)
    if not membership:
        return jsonify({"error": "You are not a member of this organization"}), 403

    members = OrganizationMember.query.filter_by(org_id=org_id).all()
    return jsonify({
        "members": [_format_member(m) for m in members],
        "total": len(members),
    }), 200


@orgs_bp.route('/organizations/<org_id>/members', methods=['POST'])
@require_auth
def add_member(org_id):
    """Add a member to an organization (owner/admin only).

    Expects { user_id: str, role: str } in the request body.
    """
    org, err = _require_org_admin(org_id)
    if err:
        return err

    data = request.get_json() or {}
    target_user_id = data.get('user_id')
    role = data.get('role', 'viewer')

    if not target_user_id:
        return jsonify({"error": "user_id is required"}), 400
    if role not in ORG_ROLES:
        return jsonify({"error": f"Invalid role. Must be one of: {', '.join(sorted(ORG_ROLES))}"}), 400

    target_user = User.query.get(target_user_id)
    if not target_user:
        return jsonify({"error": "User not found"}), 404
    if target_user.role != 'recruiter':
        return jsonify({"error": "Only recruiters can be added to organizations"}), 400

    existing = _get_membership(org_id, target_user_id)
    if existing:
        return jsonify({"error": "User is already a member of this organization"}), 409

    membership = OrganizationMember(
        org_id=org_id,
        user_id=target_user_id,
        role=role,
        invited_by=g.current_user_id,
    )
    db.session.add(membership)
    _log_org_audit(g.current_user_id, 'member_added', org.org_id,
                   {"user_id": target_user_id, "role": role})
    db.session.commit()

    return jsonify({"message": "Member added", **_format_member(membership)}), 201


@orgs_bp.route('/organizations/<org_id>/members/<membership_id>', methods=['PUT'])
@require_auth
def update_member_role(org_id, membership_id):
    """Update a member's role (owner/admin only)."""
    org, err = _require_org_admin(org_id)
    if err:
        return err

    membership = OrganizationMember.query.get(membership_id)
    if not membership or str(membership.org_id) != org_id:
        return jsonify({"error": "Membership not found"}), 404

    data = request.get_json() or {}
    new_role = data.get('role')
    if not new_role or new_role not in ORG_ROLES:
        return jsonify({"error": f"Invalid role. Must be one of: {', '.join(sorted(ORG_ROLES))}"}), 400

    old_role = membership.role
    membership.role = new_role
    _log_org_audit(g.current_user_id, 'member_role_changed', org.org_id,
                   {"user_id": str(membership.user_id), "old_role": old_role, "new_role": new_role})
    db.session.commit()

    return jsonify({"message": "Role updated", **_format_member(membership)}), 200


@orgs_bp.route('/organizations/<org_id>/members/<membership_id>', methods=['DELETE'])
@require_auth
def remove_member(org_id, membership_id):
    """Remove a member from an organization (owner/admin, or self-leave)."""
    org, err = _get_org_or_404(org_id)
    if err:
        return err

    membership = OrganizationMember.query.get(membership_id)
    if not membership or str(membership.org_id) != org_id:
        return jsonify({"error": "Membership not found"}), 404

    # Self-leave: any member can leave (except the last owner)
    is_self = str(membership.user_id) == g.current_user_id
    if is_self:
        if membership.role == 'owner':
            owner_count = OrganizationMember.query.filter_by(
                org_id=org_id, role='owner'
            ).count()
            if owner_count <= 1:
                return jsonify({"error": "Cannot leave: you are the only owner. Transfer ownership first."}), 400
    else:
        # Removing someone else requires admin access
        admin_membership = _get_membership(org_id, g.current_user_id)
        if not admin_membership or admin_membership.role not in ADMIN_ORG_ROLES:
            return jsonify({"error": "Organization admin access required"}), 403

    _log_org_audit(g.current_user_id, 'member_removed', org.org_id,
                   {"user_id": str(membership.user_id)})
    db.session.delete(membership)
    db.session.commit()

    return jsonify({"message": "Member removed"}), 200


# ---------------------------------------------------------------------------
# Organization-scoped jobs (shared job pools)
# ---------------------------------------------------------------------------

@orgs_bp.route('/organizations/<org_id>/jobs', methods=['GET'])
@require_auth
def list_org_jobs(org_id):
    """List all jobs posted by members of the organization."""
    _org, err = _get_org_or_404(org_id)
    if err:
        return err
    membership = _get_membership(org_id, g.current_user_id)
    if not membership:
        return jsonify({"error": "You are not a member of this organization"}), 403

    # Get all recruiter IDs who are org members
    member_user_ids = [m.user_id for m in OrganizationMember.query.filter_by(org_id=org_id).all()]
    recruiter_ids = [r.user_id for r in Recruiter.query.filter(
        Recruiter.user_id.in_(member_user_ids)
    ).all()]

    # Jobs from org members or explicitly assigned to this org
    query = Job.query.filter(
        db.or_(
            Job.recruiter_id.in_(recruiter_ids),
            Job.organization_id == org_id,
        )
    ).order_by(Job.created_at.desc())

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "jobs": [format_job(j) for j in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages,
    }), 200


@orgs_bp.route('/organizations/<org_id>/jobs', methods=['POST'])
@require_auth
def create_org_job(org_id):
    """Create a job and assign it to the organization.

    The job is owned by the recruiter who creates it but visible to all org members.
    """
    org, err = _get_org_or_404(org_id)
    if err:
        return err
    membership = _get_membership(org_id, g.current_user_id)
    if not membership:
        return jsonify({"error": "You are not a member of this organization"}), 403
    if membership.role not in {'owner', 'admin', 'hiring_manager'}:
        return jsonify({"error": "Only owners, admins, and hiring managers can post jobs"}), 403

    data = request.get_json() or {}
    data['organization_id'] = str(org_id)

    from models import Job as JobModel
    from models import Skill
    from routes_common import create_rankings_for_job, set_job_search_vector

    title = data.get('title')
    if not title:
        return jsonify({"error": "Missing job title"}), 400

    new_job = JobModel(
        recruiter_id=g.current_user_id,
        organization_id=org_id,
        title=title,
        description=data.get('description', ''),
        location=data.get('location', ''),
        job_type=data.get('job_type', ''),
        experience_level=data.get('experience_level', ''),
        salary_min=float(data['salary_min']) if data.get('salary_min') else None,
        salary_max=float(data['salary_max']) if data.get('salary_max') else None,
    )

    for skill_name in data.get('skills', []):
        if not skill_name.strip():
            continue
        skill = Skill.query.filter_by(skill_name=skill_name.lower()).first()
        if not skill:
            skill = Skill(skill_name=skill_name.lower())
            db.session.add(skill)
        if skill not in new_job.skills:
            new_job.skills.append(skill)

    db.session.add(new_job)
    set_job_search_vector(new_job)
    _log_org_audit(g.current_user_id, 'org_job_created', org.org_id, {"job_title": title})
    db.session.commit()
    create_rankings_for_job(new_job.job_id)

    return jsonify({
        "message": "Job posted to organization",
        "job_id": str(new_job.job_id),
        "title": new_job.title,
        "organization_id": str(org_id),
    }), 201


# ---------------------------------------------------------------------------
# Team dashboard
# ---------------------------------------------------------------------------

@orgs_bp.route('/organizations/<org_id>/dashboard', methods=['GET'])
@require_auth
def org_dashboard(org_id):
    """Aggregated team stats for the organization dashboard."""
    org, err = _get_org_or_404(org_id)
    if err:
        return err
    membership = _get_membership(org_id, g.current_user_id)
    if not membership:
        return jsonify({"error": "You are not a member of this organization"}), 403

    member_user_ids = [m.user_id for m in OrganizationMember.query.filter_by(org_id=org_id).all()]
    recruiter_ids = [r.user_id for r in Recruiter.query.filter(
        Recruiter.user_id.in_(member_user_ids)
    ).all()]

    # Jobs from org members
    org_job_ids = [j.job_id for j in Job.query.filter(
        db.or_(Job.recruiter_id.in_(recruiter_ids), Job.organization_id == org_id)
    ).all()]

    total_members = len(member_user_ids)
    total_jobs = len(org_job_ids)

    # Applications across org jobs
    total_applications = 0
    status_breakdown = {}
    if org_job_ids:
        apps = JobApplication.query.filter(JobApplication.job_id.in_(org_job_ids)).all()
        total_applications = len(apps)
        for app in apps:
            status_breakdown[app.status] = status_breakdown.get(app.status, 0) + 1

    # Total candidates (unique applicants across org jobs)
    unique_applicants = set()
    if org_job_ids:
        for app in JobApplication.query.filter(JobApplication.job_id.in_(org_job_ids)).all():
            unique_applicants.add(str(app.applicant_id))

    # Weekly trend — jobs posted in last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    jobs_this_week = Job.query.filter(
        db.or_(Job.recruiter_id.in_(recruiter_ids), Job.organization_id == org_id),
        Job.created_at >= week_ago,
    ).count()

    # Average match score across org rankings
    avg_score = 0.0
    if org_job_ids:
        result = db.session.query(func.avg(Ranking.matching_score)).filter(
            Ranking.job_id.in_(org_job_ids)
        ).scalar()
        avg_score = round(float(result or 0), 2)

    return jsonify({
        "org_id": str(org_id),
        "org_name": org.name,
        "total_members": total_members,
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "unique_applicants": len(unique_applicants),
        "application_status_breakdown": status_breakdown,
        "jobs_posted_this_week": jobs_this_week,
        "avg_match_score": avg_score,
    }), 200
