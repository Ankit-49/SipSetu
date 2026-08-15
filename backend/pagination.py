"""Standardized ``{ data, meta }`` response envelope + cursor pagination (Phase 4.2).

The API blueprint is registered twice — canonical ``api`` (``/api/v1``) and
legacy ``api_legacy`` (``/api``). The new envelope and cursor pagination apply
to the canonical prefix only; the legacy prefix keeps its historical shapes so
old clients are unaffected during the deprecation window.

Cursor pagination is keyset (seek) based: the cursor encodes the ordering-key
tuple of the last item returned, and the next page is fetched with a
``WHERE (k1, k2, ...) < (:v1, :v2, ...)`` predicate (descending) — O(1) per
page regardless of dataset size, stable under concurrent inserts.
"""

import base64
import json
from datetime import datetime

from flask import request
from sqlalchemy import and_, or_

# The canonical blueprint is registered with name 'api'; the legacy alias with
# 'api_legacy' (see app.py). request.blueprint tells the two apart.
CANONICAL_BLUEPRINT = "api"


def is_v1_request() -> bool:
    """True when the current request hit the canonical /api/v1 prefix."""
    return request.blueprint == CANONICAL_BLUEPRINT


def parse_limit(default: int = 20, maximum: int = 100) -> int:
    """Parse the ``?limit=`` query param with sane clamps."""
    try:
        limit = int(request.args.get("limit", default))
    except (TypeError, ValueError):
        limit = default
    return min(max(limit, 1), maximum)


# ---------------------------------------------------------------------------
# Cursor encoding
# ---------------------------------------------------------------------------


def _serialize(value):
    if isinstance(value, datetime):
        return {"t": "dt", "v": value.isoformat()}
    if isinstance(value, bool):
        return {"t": "b", "v": value}
    if isinstance(value, (int, float)):
        return {"t": "n", "v": value}
    return {"t": "s", "v": str(value)}


def _deserialize(spec):
    if not isinstance(spec, dict) or "t" not in spec:
        return None
    if spec["t"] == "dt":
        try:
            return datetime.fromisoformat(spec["v"])
        except (TypeError, ValueError):
            return None
    return spec["v"]


def encode_cursor(*values) -> str:
    """Encode an ordering-key tuple into an opaque, URL-safe cursor string."""
    payload = {"keys": [_serialize(v) for v in values]}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_cursor(cursor):
    """Decode a cursor back to a typed list of ordering keys (None if invalid)."""
    if not cursor:
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode("ascii")))
        keys = [_deserialize(k) for k in payload.get("keys", [])]
        if keys and all(k is not None for k in keys):
            return keys
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Keyset (seek) filtering
# ---------------------------------------------------------------------------


def keyset_filter(query, columns, cursor_values, descending=True):
    """Restrict ``query`` to rows strictly after the cursor position.

    ``columns`` are the SQLAlchemy columns forming the ordering key (primary
    sort column first, tiebreaker last); ``cursor_values`` is the decoded
    cursor from ``decode_cursor``. Produces a tuple comparison predicate that
    works on both Postgres and SQLite.
    """
    if not columns or len(columns) != len(cursor_values):
        return query

    def less(a, b):
        return a < b if descending else a > b

    clauses = []
    for i, (col, val) in enumerate(zip(columns, cursor_values, strict=True)):
        prefix = [columns[j] == cursor_values[j] for j in range(i)]
        clauses.append(and_(*prefix, less(col, val)))
    return query.filter(or_(*clauses))


def in_memory_after(items, key_fn, cursor_values, descending=True):
    """Filter an already-sorted in-memory list to rows strictly after the cursor."""
    cursor = tuple(cursor_values)
    result = []
    for item in items:
        key = tuple(key_fn(item))
        if (key < cursor) if descending else (key > cursor):
            result.append(item)
    return result


# ---------------------------------------------------------------------------
# Response envelope
# ---------------------------------------------------------------------------


def build_envelope(data, total=None, limit=None, next_cursor=None, has_more=None, **meta_extra):
    """Build the standardized ``{ data, meta }`` response body.

    ``meta.pagination`` carries ``total`` (rows after the cursor), ``limit``,
    ``next_cursor`` and ``has_more``. Extra keyword arguments land in ``meta``
    alongside ``pagination`` (e.g. filter dropdowns or related ids).
    """
    pagination = {}
    if total is not None:
        pagination["total"] = total
    if limit is not None:
        pagination["limit"] = limit
    # Always present so clients can rely on a uniform shape (None = no more).
    pagination["next_cursor"] = next_cursor
    pagination["has_more"] = (
        has_more if has_more is not None else next_cursor is not None
    )

    meta = {}
    if pagination:
        meta["pagination"] = pagination
    meta.update(meta_extra)
    return {"data": data, "meta": meta}
