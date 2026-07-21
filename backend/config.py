import os


class Config:
    SECRET_KEY = os.environ.get(
        'JWT_SECRET_KEY',
        'sipsetu-dev-jwt-secret-change-in-production'
    )
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24
    DATABASE_URL = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/sipsetu'
    )
    RESET_TOKEN_EXPIRY_HOURS = 1
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
