#!/usr/bin/env python3
"""
SipSetu Health Check Script

Comprehensive health check for all services.
Usage: python scripts/health_check.py [--url URL] [--verbose]

Exit codes:
  0 - All checks passed
  1 - One or more checks failed
"""

import argparse
import sys
import time
from urllib.parse import urljoin

import requests


def check_endpoint(url: str, timeout: int = 5) -> dict:
    """Check a single endpoint."""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        duration_ms = (time.time() - start_time) * 1000

        return {
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "response": response.json() if response.headers.get("content-type", "").startswith("application/json") else None,
        }
    except requests.exceptions.Timeout:
        return {
            "status": "unhealthy",
            "error": "Request timed out",
            "duration_ms": timeout * 1000,
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "unhealthy",
            "error": "Connection refused",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


def check_database(health_url: str) -> dict:
    """Check database health via health endpoint."""
    result = check_endpoint(health_url)
    if result.get("response", {}).get("checks", {}).get("database") == "ok":
        return {"status": "healthy", "message": "Database connection OK"}
    return {"status": "unhealthy", "message": result.get("response", {}).get("checks", {}).get("database", "Unknown")}


def check_redis(health_url: str) -> dict:
    """Check Redis health via health endpoint."""
    result = check_endpoint(health_url)
    if result.get("response", {}).get("checks", {}).get("redis") == "ok":
        return {"status": "healthy", "message": "Redis connection OK"}
    return {"status": "unhealthy", "message": result.get("response", {}).get("checks", {}).get("redis", "Unknown")}


def main():
    parser = argparse.ArgumentParser(description="SipSetu Health Check")
    parser.add_argument("--url", default="http://localhost:5000", help="Backend URL")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    health_url = urljoin(base_url, "/api/health")

    print(f"🏥 SipSetu Health Check")
    print(f"   URL: {base_url}")
    print(f"   Timeout: {args.timeout}s")
    print("-" * 50)

    checks = []

    # 1. Main health endpoint
    print("1️⃣  Checking health endpoint...")
    result = check_endpoint(health_url, args.timeout)
    checks.append(("Health Endpoint", result["status"], result))

    if result["status"] == "healthy":
        print(f"   ✅ Healthy ({result.get('duration_ms', 'N/A')}ms)")
        if args.verbose and result.get("response"):
            print(f"   Version: {result['response'].get('version', 'unknown')}")
    else:
        print(f"   ❌ Unhealthy: {result.get('error', result.get('status_code', 'Unknown'))}")

    # 2. Database check
    print("\n2️⃣  Checking database...")
    db_result = check_database(health_url)
    checks.append(("Database", db_result["status"], db_result))

    if db_result["status"] == "healthy":
        print(f"   ✅ {db_result['message']}")
    else:
        print(f"   ❌ {db_result['message']}")

    # 3. Redis check
    print("\n3️⃣  Checking Redis...")
    redis_result = check_redis(health_url)
    checks.append(("Redis", redis_result["status"], redis_result))

    if redis_result["status"] == "healthy":
        print(f"   ✅ {redis_result['message']}")
    else:
        print(f"   ❌ {redis_result['message']}")

    # 4. API endpoints check
    print("\n4️⃣  Checking API endpoints...")
    api_endpoints = [
        "/api/v1/jobs",
        "/api/v1/users/me",
        "/api/v1/resumes",
    ]

    for endpoint in api_endpoints:
        url = urljoin(base_url, endpoint)
        result = check_endpoint(url, args.timeout)
        status = "✅" if result["status_code"] in [200, 401, 403] else "❌"
        checks.append((f"API {endpoint}", "healthy" if result["status_code"] in [200, 401, 403] else "unhealthy", result))
        print(f"   {status} {endpoint}: {result['status_code']} ({result.get('duration_ms', 'N/A')}ms)")

    # Summary
    print("\n" + "=" * 50)
    healthy_count = sum(1 for _, status, _ in checks if status == "healthy")
    total_count = len(checks)

    if healthy_count == total_count:
        print(f"✅ All checks passed ({healthy_count}/{total_count})")
        return 0
    else:
        print(f"❌ Some checks failed ({healthy_count}/{total_count} passed)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
