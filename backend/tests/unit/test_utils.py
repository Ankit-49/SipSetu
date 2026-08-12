"""Unit tests for authentication and utility functions."""

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, request

from auth_middleware import create_token, decode_token
from rate_limiter import rate_limit
from utils.email import send_email
from utils.parser import extract_text


class TestAuthMiddleware:
    """Tests for JWT token creation and validation."""

    def test_create_token(self, app):
        token = create_token("user-123", "applicant")
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self, app):
        token = create_token("user-123", "applicant")
        payload = decode_token(token)
        assert payload["user_id"] == "user-123"
        assert payload["role"] == "applicant"

    def test_decode_invalid_token(self, app):
        with pytest.raises(Exception):
            decode_token("invalid.token.string")

    def test_decode_expired_token(self, app):
        import time

        import jwt
        payload = {"user_id": "user-123", "role": "applicant", "exp": int(time.time()) - 3600}
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        with pytest.raises(Exception):
            decode_token(token)


class TestRateLimiter:
    """Tests for rate limiting functionality."""

    def test_rate_limit_allows_within_limit(self):
        app = Flask(__name__)
        with app.test_request_context("/", method="POST", json={"email": "test@test.com"}):
            request.remote_addr = "127.0.0.1"

            @rate_limit(max_requests=5, window_seconds=60, key_by="ip")
            def test_route():
                return "OK"

            # First request should succeed
            result = test_route()
            assert result == "OK"

    def test_rate_limit_blocks_over_limit(self):
        app = Flask(__name__)
        with app.test_request_context("/", method="POST", json={"email": "test@test.com"}):
            request.remote_addr = "127.0.0.1"

            @rate_limit(max_requests=2, window_seconds=60, key_by="ip")
            def test_route():
                return "OK"

            test_route()  # 1st request
            test_route()  # 2nd request

            # 3rd request should be blocked
            result = test_route()
            assert result[1] == 429


class TestEmailUtils:
    """Tests for email utility functions."""

    @patch("utils.email.smtplib.SMTP")
    def test_send_email_with_smtp(self, mock_smtp):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        import os
        os.environ["SMTP_HOST"] = "smtp.test.com"
        os.environ["SMTP_PORT"] = "587"
        os.environ["SMTP_USER"] = "test@test.com"
        os.environ["SMTP_PASSWORD"] = "password"

        result = send_email("to@test.com", "Test Subject", "<p>HTML</p>", "Text")
        assert result is True
        mock_server.send_message.assert_called_once()

    def test_send_email_dev_fallback(self, capsys):
        # No SMTP config - should print to stderr
        import os
        if "SMTP_HOST" in os.environ:
            del os.environ["SMTP_HOST"]

        result = send_email("to@test.com", "Test", "<p>HTML</p>")
        assert result is True

        captured = capsys.readouterr()
        assert "EMAIL TO: to@test.com" in captured.err
        assert "Test" in captured.err


class TestParser:
    """Tests for document parsing."""

    def test_extract_text_pdf_not_found(self):
        with pytest.raises(FileNotFoundError):
            extract_text("/nonexistent/file.pdf")

    def test_extract_text_unsupported_type(self):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test")
            f.flush()
            with pytest.raises(ValueError, match="Unsupported file type"):
                extract_text(f.name)


# Tests for ranking_ml module
class TestRankingML:
    """Tests for ML ranking functionality."""

    def test_feature_order(self):
        from ranking_ml import _feature_order
        features = _feature_order()
        assert len(features) == 17
        assert "skills_coverage" in features
        assert "experience_years" in features
        assert "skill_specificity" in features

    def test_specificity_score(self):
        from ranking_ml import _specificity_score
        idf = {"python": 2.0, "react": 1.5, "communication": 0.5}
        resume_skills = ["python", "react"]
        job_skills = ["python", "react", "communication"]
        score = _specificity_score(resume_skills, job_skills, idf)
        # (2.0 + 1.5) / (2.0 + 1.5 + 0.5) * 100 = 3.5 / 4.0 * 100 = 87.5
        assert abs(score - 87.5) < 0.1

    def test_title_similarity(self):
        from ranking_ml import _title_similarity
        job = MagicMock()
        job.title = "Senior Python Developer"
        resume_text = "Experienced python developer with 5 years"
        score = _title_similarity(resume_text, job)
        # Words: senior, python, developer -> python, developer match = 2/3 = 66.67
        assert score > 0

    def test_keyword_density(self):
        from ranking_ml import _keyword_density
        job = MagicMock()
        job.description = "We need python and react skills"
        resume_text = "I know python well"
        score = _keyword_density(resume_text, job)
        assert score > 0