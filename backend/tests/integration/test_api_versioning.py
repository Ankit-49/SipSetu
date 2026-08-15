"""Integration tests for Phase 4.1: API versioning, deprecation headers, and OpenAPI docs."""

from uuid import uuid4


class TestVersionPrefix:
    """Both the canonical /api/v1 prefix and the legacy /api prefix must work."""

    def test_v1_login_works(self, client, test_user):
        response = client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.get_json()
        assert "token" in data

    def test_v1_me_works(self, client, auth_headers):
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.get_json()["email"] == "test@example.com"

    def test_legacy_login_still_works(self, client, test_user):
        response = client.post("/api/auth/login", json={
            "email": test_user.email,
            "password": "password123",
        })
        assert response.status_code == 200
        assert "token" in response.get_json()

    def test_v1_register(self, client):
        email = f"v1user{uuid4().hex[:8]}@test.com"
        response = client.post("/api/v1/auth/register", json={
            "name": "V1 User",
            "email": email,
            "password": "password123",
            "role": "applicant",
        })
        assert response.status_code == 201
        assert response.get_json()["email"] == email

    def test_v1_jobs_list(self, client, test_job):
        response = client.get("/api/v1/jobs")
        assert response.status_code == 200
        assert len(response.get_json()["jobs"]) >= 1


class TestDeprecationHeaders:
    """RFC 8594 headers on the legacy /api prefix, absent on /api/v1."""

    def test_legacy_gets_deprecation_headers(self, client, test_user):
        response = client.post("/api/auth/login", json={
            "email": test_user.email,
            "password": "password123",
        })
        assert response.status_code == 200
        assert response.headers.get("Deprecation") == "true"
        assert "Sunset" in response.headers
        link = response.headers.get("Link", "")
        assert 'rel="successor-version"' in link
        assert "/api/v1/auth/login" in link

    def test_v1_has_no_deprecation_headers(self, client, test_user):
        response = client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "password123",
        })
        assert response.status_code == 200
        assert "Deprecation" not in response.headers
        assert "Sunset" not in response.headers
        assert "Link" not in response.headers

    def test_health_check_has_no_deprecation_headers(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert "Deprecation" not in response.headers
        assert "Sunset" not in response.headers


class TestOpenAPIDocs:
    """Swagger UI + OpenAPI spec, documenting only the canonical v1 surface."""

    def test_swagger_ui_served(self, client):
        response = client.get("/apidocs/")
        assert response.status_code == 200
        assert b"Swagger" in response.data or b"swagger" in response.data

    def test_apispec_contains_v1_auth_paths(self, client):
        response = client.get("/apispec.json")
        assert response.status_code == 200
        spec = response.get_json()
        assert "paths" in spec
        assert "/api/v1/auth/register" in spec["paths"]
        assert "/api/v1/auth/login" in spec["paths"]
        assert "/api/v1/auth/me" in spec["paths"]

    def test_apispec_excludes_legacy_paths(self, client):
        response = client.get("/apispec.json")
        assert response.status_code == 200
        spec = response.get_json()
        paths = spec["paths"]
        assert "/api/auth/login" not in paths
        assert "/api/auth/register" not in paths
        # No path should carry the legacy /api/ prefix at all.
        assert not any(p.startswith("/api/") and not p.startswith("/api/v1/") for p in paths)

    def test_apispec_has_metadata_and_security(self, client):
        response = client.get("/apispec.json")
        assert response.status_code == 200
        spec = response.get_json()
        assert spec["info"]["title"] == "SipSetu API"
        assert "version" in spec["info"]
        assert "BearerAuth" in spec.get("securityDefinitions", {})

    def test_apispec_has_schema_definitions(self, client):
        response = client.get("/apispec.json")
        assert response.status_code == 200
        spec = response.get_json()
        defs = spec.get("definitions", {})
        assert "Error" in defs
        # The register/login request + response schemas should be embedded.
        assert any(name in defs for name in ("RegisterRequest", "LoginRequest", "AuthResponse", "MeResponse"))
