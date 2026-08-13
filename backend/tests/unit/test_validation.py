"""Unit tests for request validation, auth decorators, and parsing."""

import io
from unittest.mock import patch

import pytest
from flask import Flask, g, jsonify

from auth_middleware import create_token, extract_token, require_auth, require_role
from validation import (
    get_validated_data,
    get_validated_file,
    get_validated_query,
    validate_file_upload,
    validate_json,
    validate_query,
)


class TestValidateJson:
    """Tests for the JSON body validation decorator."""

    def _app(self):
        app = Flask(__name__)
        app.config["JWT_EXPIRATION_HOURS"] = 24
        app.config["SECRET_KEY"] = "test-secret-key-for-validation"
        app.config["JWT_ALGORITHM"] = "HS256"
        return app

    def test_missing_content_type(self):
        app = self._app()

        class Schema:
            def __init__(self, **kwargs):
                self.name = kwargs.get("name")

        @app.post("/test")
        @validate_json(Schema)
        def endpoint():
            return "OK"

        client = app.test_client()
        resp = client.post("/test", data="name=test", content_type="application/x-www-form-urlencoded")
        assert resp.status_code == 400
        assert "Content-Type must be application/json" in resp.get_json()["error"]

    def test_valid_json_sets_g(self):
        app = self._app()

        class Schema:
            def __init__(self, **kwargs):
                self.name = kwargs.get("name")

        @app.post("/test")
        @validate_json(Schema)
        def endpoint():
            return jsonify(name=get_validated_data().name)

        client = app.test_client()
        resp = client.post("/test", json={"name": "Jane"})
        assert resp.status_code == 200
        assert resp.get_json()["name"] == "Jane"

    def test_invalid_json_returns_errors(self):
        import pydantic
        app = self._app()

        class Schema(pydantic.BaseModel):
            name: str

        @app.post("/test")
        @validate_json(Schema)
        def endpoint():
            return "OK"

        client = app.test_client()
        resp = client.post("/test", json={"email": "x@y.com"})
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "Validation failed"

    def test_unexpected_error_returns_400(self):
        app = self._app()

        class Schema:
            def __init__(self, **kwargs):
                raise RuntimeError("boom")

        @app.post("/test")
        @validate_json(Schema)
        def endpoint():
            return "OK"

        client = app.test_client()
        with patch("validation.logger"):
            resp = client.post("/test", json={"name": "Jane"})
        assert resp.status_code == 400
        assert "Validation error" in resp.get_json()["error"]


class TestValidateQuery:
    """Tests for the query parameter validation decorator."""

    def test_valid_query_sets_g(self):
        app = Flask(__name__)

        class Schema:
            def __init__(self, **kwargs):
                self.page = int(kwargs.get("page", 1))

        @app.get("/test")
        @validate_query(Schema)
        def endpoint():
            return jsonify(page=get_validated_query().page)

        client = app.test_client()
        resp = client.get("/test?page=3")
        assert resp.status_code == 200
        assert resp.get_json()["page"] == 3

    def test_multi_value_query(self):
        app = Flask(__name__)

        class Schema:
            def __init__(self, **kwargs):
                self.tags = kwargs.get("tags")

        @app.get("/test")
        @validate_query(Schema)
        def endpoint():
            return jsonify(tags=get_validated_query().tags)

        client = app.test_client()
        resp = client.get("/test?tags=a&tags=b")
        assert resp.status_code == 200
        assert resp.get_json()["tags"] == ["a", "b"]

    def test_invalid_query_returns_400(self):
        import pydantic
        app = Flask(__name__)

        class Schema(pydantic.BaseModel):
            page: int

        @app.get("/test")
        @validate_query(Schema)
        def endpoint():
            return "OK"

        client = app.test_client()
        resp = client.get("/test?page=abc")
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "Query validation failed"

    def test_no_query_params(self):
        app = Flask(__name__)

        class Schema:
            def __init__(self, **kwargs):
                self.ready = True

        @app.get("/test")
        @validate_query(Schema)
        def endpoint():
            return "OK"

        client = app.test_client()
        resp = client.get("/test")
        assert resp.status_code == 200


class TestValidateFileUpload:
    """Tests for the file upload validation decorator."""

    def test_no_file_required(self):
        app = Flask(__name__)

        @app.post("/test")
        @validate_file_upload(required=True)
        def endpoint():
            return "OK"

        client = app.test_client()
        resp = client.post("/test", data={}, content_type="multipart/form-data")
        assert resp.status_code == 400
        assert "No file uploaded" in resp.get_json()["error"]

    def test_no_file_optional(self):
        app = Flask(__name__)

        @app.post("/test")
        @validate_file_upload(required=False)
        def endpoint():
            return "OK"

        client = app.test_client()
        resp = client.post("/test", data={}, content_type="multipart/form-data")
        assert resp.status_code == 200

    def test_bad_extension(self):
        app = Flask(__name__)

        @app.post("/test")
        @validate_file_upload(allowed_extensions=[".pdf", ".docx", ".txt"])
        def endpoint():
            return "OK"

        client = app.test_client()
        resp = client.post(
            "/test",
            data={"file": (io.BytesIO(b"evil"), "evil.exe")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        assert "File type not allowed" in resp.get_json()["error"]

    def test_oversized_file(self):
        app = Flask(__name__)

        @app.post("/test")
        @validate_file_upload(max_size_mb=1)
        def endpoint():
            return "OK"

        big = b"x" * (2 * 1024 * 1024)
        client = app.test_client()
        resp = client.post(
            "/test",
            data={"file": (io.BytesIO(big), "big.pdf")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        assert "File size exceeds" in resp.get_json()["error"]

    def test_valid_file_sets_g(self):
        app = Flask(__name__)

        @app.post("/test")
        @validate_file_upload()
        def endpoint():
            info = get_validated_file()
            return jsonify(filename=info["filename"], extension=info["extension"])

        client = app.test_client()
        resp = client.post(
            "/test",
            data={"file": (io.BytesIO(b"hello"), "doc.txt")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert resp.get_json()["filename"] == "doc.txt"
        assert resp.get_json()["extension"] == ".txt"

    def test_filename_without_dot(self):
        app = Flask(__name__)

        @app.post("/test")
        @validate_file_upload()
        def endpoint():
            info = get_validated_file()
            return jsonify(extension=info["extension"])

        client = app.test_client()
        resp = client.post(
            "/test",
            data={"file": (io.BytesIO(b"hello"), "README")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400  # no extension -> not allowed


class TestAuthDecorators:
    """Tests for JWT auth decorators and token extraction."""

    def _app(self):
        app = Flask(__name__)
        app.config["JWT_EXPIRATION_HOURS"] = 24
        app.config["SECRET_KEY"] = "test-secret-key-32-chars-minimum-length"
        app.config["JWT_ALGORITHM"] = "HS256"
        return app

    def test_extract_token_bearer(self):
        app = self._app()
        with app.test_request_context(headers={"Authorization": "Bearer abc.def.ghi"}):
            assert extract_token() == "abc.def.ghi"

    def test_extract_token_missing(self):
        app = self._app()
        with app.test_request_context():
            assert extract_token() is None

    def test_extract_token_wrong_prefix(self):
        app = self._app()
        with app.test_request_context(headers={"Authorization": "Basic abcdef"}):
            assert extract_token() is None

    def test_require_auth_missing_token(self):
        app = self._app()

        @app.get("/protected")
        @require_auth
        def endpoint():
            return "OK"

        client = app.test_client()
        resp = client.get("/protected")
        assert resp.status_code == 401

    def test_require_auth_valid_token(self):
        app = self._app()

        @app.get("/protected")
        @require_auth
        def endpoint():
            return jsonify(uid=g.current_user_id, role=g.current_user_role)

        with app.app_context():
            token = create_token("user-9", "applicant")
        client = app.test_client()
        resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.get_json() == {"uid": "user-9", "role": "applicant"}

    def test_require_auth_expired_token(self):
        import time

        import jwt
        app = self._app()
        payload = {"user_id": "u1", "role": "applicant", "exp": int(time.time()) - 3600}
        token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")

        @app.get("/protected")
        @require_auth
        def endpoint():
            return "OK"

        client = app.test_client()
        resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_require_auth_invalid_token(self):
        app = self._app()

        @app.get("/protected")
        @require_auth
        def endpoint():
            return "OK"

        client = app.test_client()
        resp = client.get("/protected", headers={"Authorization": "Bearer not.a.jwt"})
        assert resp.status_code == 401

    def test_require_role_wrong_role(self):
        app = self._app()

        @app.get("/recruiter-only")
        @require_role("recruiter")
        def endpoint():
            return "OK"

        with app.app_context():
            token = create_token("user-1", "applicant")
        client = app.test_client()
        resp = client.get("/recruiter-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_require_role_correct_role(self):
        app = self._app()

        @app.get("/recruiter-only")
        @require_role("recruiter")
        def endpoint():
            return "OK"

        with app.app_context():
            token = create_token("user-2", "recruiter")
        client = app.test_client()
        resp = client.get("/recruiter-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
