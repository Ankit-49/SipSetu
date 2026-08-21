"""LLM-based resume parser (Phase 5.1).

Extracts structured data from resume text using an LLM (OpenAI-compatible
API). Falls back to regex-based extraction when no LLM provider is
configured, so the feature degrades gracefully.

Usage:
    result = parse_resume(text)
    # result = {
    #   "sections": {"summary": ..., "experience": [...], "education": [...],
    #                "skills": [...], "projects": [...]},
    #   "confidence": 0.85,
    #   "extraction_method": "llm" | "regex"
    # }
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Structured extraction prompt
# ---------------------------------------------------------------------------

_PARSE_PROMPT = """\
You are a resume parsing expert. Extract structured data from the following resume text.
Return ONLY valid JSON with these keys:
{
  "summary": "professional summary or null",
  "experience": [
    {
      "title": "job title",
      "company": "company name",
      "duration": "e.g. 2020-2023 or 3 years",
      "description": "key responsibilities and achievements",
      "skills_used": ["skill1", "skill2"]
    }
  ],
  "education": [
    {
      "degree": "degree name",
      "institution": "school/university",
      "year": "graduation year or range",
      "gpa": "GPA if mentioned, else null"
    }
  ],
  "skills": ["skill1", "skill2", ...],
  "projects": [
    {
      "name": "project name",
      "description": "brief description",
      "technologies": ["tech1", "tech2"]
    }
  ],
  "certifications": ["cert1", "cert2"],
  "languages": ["language1", "language2"]
}

Resume text:
---
{resume_text}
---

Return ONLY the JSON object, no markdown fences or extra text."""


# ---------------------------------------------------------------------------
# LLM provider
# ---------------------------------------------------------------------------

def _call_llm(prompt: str) -> str | None:
    """Call an OpenAI-compatible chat completion API.

    Supports OPENAI_API_KEY (default endpoint) or a custom
    LLM_BASE_URL + LLM_API_KEY combination.
    """
    api_key = getattr(settings, "LLM_API_KEY", None) or getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        return None

    base_url = getattr(settings, "LLM_BASE_URL", "https://api.openai.com/v1")
    model = getattr(settings, "LLM_MODEL", "gpt-4o-mini")

    try:
        import httpx
        response = httpx.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 4000,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning(f"LLM call failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Regex-based fallback parser
# ---------------------------------------------------------------------------

_SECTION_HEADERS = re.compile(
    r"^(?:#{1,3}\s+)?"
    r"(summary|professional summary|objective|experience|work experience|"
    r"employment|education|academic|skills|technical skills|projects|"
    r"certifications?|languages?|awards?|interests?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

_EXPERIENCE_PATTERN = re.compile(
    r"(?:(?:senior|lead|principal|staff|junior|associate|chief)?\s*"
    r"(?:software|data|backend|frontend|full[\s-]?stack|devops|"
    r"machine learning|product|project|business|systems?|network|"
    r"cloud|security|QA|testing)\s*(?:engineer|developer|architect|"
    r"analyst|manager|consultant|scientist|designer|administrator)?)",
    re.IGNORECASE,
)


def _regex_parse(text: str) -> dict[str, Any]:
    """Best-effort regex extraction as fallback when no LLM is available."""
    sections: dict[str, Any] = {
        "summary": None,
        "experience": [],
        "education": [],
        "skills": [],
        "projects": [],
        "certifications": [],
        "languages": [],
    }

    # Extract sections by headers
    parts = _SECTION_HEADERS.split(text)
    headers = _SECTION_HEADERS.findall(text)

    for i, header in enumerate(headers):
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        h_lower = header.lower()

        if "summary" in h_lower or "objective" in h_lower:
            sections["summary"] = content[:500]
        elif "experience" in h_lower or "employment" in h_lower:
            # Split by bullet points or lines
            lines = [ln.strip() for ln in content.split("\n") if ln.strip()]
            current_exp: dict[str, Any] | None = None
            for line in lines:
                if _EXPERIENCE_PATTERN.search(line):
                    if current_exp:
                        sections["experience"].append(current_exp)
                    current_exp = {"title": line, "company": "", "duration": "", "description": "", "skills_used": []}
                elif current_exp is not None:
                    current_exp["description"] += " " + line
            if current_exp:
                sections["experience"].append(current_exp)
        elif "education" in h_lower or "academic" in h_lower:
            lines = [ln.strip() for ln in content.split("\n") if ln.strip()]
            for line in lines[:5]:
                sections["education"].append({
                    "degree": line, "institution": "", "year": "", "gpa": None,
                })
        elif "skill" in h_lower:
            # Extract comma or bullet-separated skills
            skill_text = re.sub(r"[•●○▪–—\-]", ",", content)  # noqa: RUF001
            skills = [s.strip() for s in skill_text.split(",") if s.strip()]
            sections["skills"] = skills[:30]
        elif "project" in h_lower:
            lines = [ln.strip() for ln in content.split("\n") if ln.strip()]
            for line in lines[:5]:
                sections["projects"].append({
                    "name": line, "description": "", "technologies": [],
                })
        elif "cert" in h_lower:
            cert_text = re.sub(r"[•●○▪–—\-]", ",", content)  # noqa: RUF001
            sections["certifications"] = [c.strip() for c in cert_text.split(",") if c.strip()]
        elif "language" in h_lower:
            lang_text = re.sub(r"[•●○▪–—\-]", ",", content)  # noqa: RUF001
            sections["languages"] = [ln.strip() for ln in lang_text.split(",") if ln.strip()]

    # Always extract skills from the full text using existing extractor
    if not sections["skills"]:
        from routes_common import extract_skills_from_text
        sections["skills"] = extract_skills_from_text(text)

    return sections


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_resume(text: str) -> dict[str, Any]:
    """Parse a resume into structured sections.

    Returns:
        {
            "sections": { ... structured data ... },
            "confidence": 0.0-1.0,
            "extraction_method": "llm" | "regex",
        }
    """
    if not text or not text.strip():
        return {
            "sections": {"summary": None, "experience": [], "education": [], "skills": [], "projects": []},
            "confidence": 0.0,
            "extraction_method": "regex",
        }

    # Try LLM first
    prompt = _PARSE_PROMPT.format(resume_text=text[:8000])  # Truncate for token limits
    llm_response = _call_llm(prompt)

    if llm_response:
        try:
            # Clean markdown fences if present
            cleaned = llm_response.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```\w*\n?", "", cleaned)
                cleaned = re.sub(r"\n?```$", "", cleaned)
            sections = json.loads(cleaned)
            # Compute confidence based on completeness
            confidence = _compute_confidence(sections)
            return {
                "sections": sections,
                "confidence": confidence,
                "extraction_method": "llm",
            }
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")

    # Fallback to regex
    sections = _regex_parse(text)
    confidence = _compute_confidence(sections)
    return {
        "sections": sections,
        "confidence": confidence,
        "extraction_method": "regex",
    }


def _compute_confidence(sections: dict[str, Any]) -> float:
    """Estimate extraction confidence based on populated sections."""
    score = 0.0
    total = 0

    # Skills are most important for matching
    total += 3
    if sections.get("skills") and len(sections["skills"]) >= 3:
        score += 3
    elif sections.get("skills"):
        score += 1.5

    # Experience
    total += 2
    if sections.get("experience") and len(sections["experience"]) >= 1:
        score += 2
    elif sections.get("experience"):
        score += 1

    # Education
    total += 1
    if sections.get("education"):
        score += 1

    # Summary
    total += 1
    if sections.get("summary"):
        score += 1

    # Projects
    total += 1
    if sections.get("projects"):
        score += 1

    return round(score / total, 2) if total > 0 else 0.0
