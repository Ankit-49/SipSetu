"""Request validation middleware using Pydantic schemas."""

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import g, jsonify, request
from pydantic import ValidationError as PydanticValidationError

# pydantic's ValidationError is aliased above so the custom ValidationError
# class defined below doesn't shadow it in the decorators' except clauses.

logger = logging.getLogger(__name__)


def validate_json(schema_class: type[Any]) -> Callable:
    """Decorator to validate request JSON body against a Pydantic schema."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400
            
            try:
                data = request.get_json()
                validated = schema_class(**data)
                g.validated_data = validated
            except PydanticValidationError as e:
                errors = []
                for error in e.errors():
                    field = ".".join(str(loc) for loc in error["loc"])
                    errors.append({
                        "field": field,
                        "message": error["msg"],
                        "type": error["type"]
                    })
                return jsonify({"error": "Validation failed", "details": errors}), 400
            except Exception as e:
                logger.exception("Validation error")
                return jsonify({"error": f"Validation error: {e!s}"}), 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


def validate_query(schema_class: type[Any]) -> Callable:
    """Decorator to validate query parameters against a Pydantic schema."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # Convert query params to dict (handling multi-value params)
                query_dict = {}
                for key, value in request.args.items(multi=True):
                    if key in query_dict:
                        if not isinstance(query_dict[key], list):
                            query_dict[key] = [query_dict[key]]
                        query_dict[key].append(value)
                    else:
                        query_dict[key] = value
                
                validated = schema_class(**query_dict)
                g.validated_query = validated
            except PydanticValidationError as e:
                errors = []
                for error in e.errors():
                    field = ".".join(str(loc) for loc in error["loc"])
                    errors.append({
                        "field": field,
                        "message": error["msg"],
                        "type": error["type"]
                    })
                return jsonify({"error": "Query validation failed", "details": errors}), 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


def get_validated_data() -> Any:
    """Get validated request data from Flask g object."""
    return getattr(g, 'validated_data', None)


def get_validated_query() -> Any:
    """Get validated query parameters from Flask g object."""
    return getattr(g, 'validated_query', None)


class ValidationError(Exception):
    """Custom validation error for manual validation."""
    def __init__(self, message: str, details: list = None):
        self.message = message
        self.details = details or []
        super().__init__(message)


def validate_file_upload(
    allowed_extensions: list = None,
    max_size_mb: int = 10,
    required: bool = True
) -> Callable:
    """Decorator to validate file uploads."""
    if allowed_extensions is None:
        allowed_extensions = ['.pdf', '.docx', '.txt']
    
    max_bytes = max_size_mb * 1024 * 1024
    
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            file = request.files.get('file')
            
            if not file or file.filename == '':
                if required:
                    return jsonify({"error": "No file uploaded"}), 400
                return f(*args, **kwargs)
            
            # Check extension
            ext = '.' + file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
            if ext not in allowed_extensions:
                return jsonify({
                    "error": f"File type not allowed. Allowed: {', '.join(allowed_extensions)}"
                }), 400
            
            # Check file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset
            
            if file_size > max_bytes:
                return jsonify({
                    "error": f"File size exceeds maximum allowed ({max_size_mb}MB)"
                }), 400
            
            # Store validated file info in g
            g.validated_file = {
                'file': file,
                'filename': file.filename,
                'size': file_size,
                'extension': ext,
            }
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


def get_validated_file() -> dict | None:
    """Get validated file info from Flask g object."""
    return getattr(g, 'validated_file', None)