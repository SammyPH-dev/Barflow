"""
Gateway Configuration Module

Every setting of the API Gateway is written here (the JWT secret is read from local_settings.py for now)

Author: Zacchary Bedard-Chenier
Date: 26/11/2026
Version: 1.0
"""

# Public prefix of every route: /api/v1/<service>/...
# Every service uses the same prefix, so the gateway forwards the path unchanged.
API_PREFIX = '/api/v1'

# Address of each service, found by the <service> part of the URL.
# Ports: the gateway is on 8000, the services on the next ports.
SERVICES = {
    'login': 'http://127.0.0.1:8001',
    'inventory': 'http://127.0.0.1:8002',
    'orders': 'http://127.0.0.1:8003',
    'recipes': 'http://127.0.0.1:8004',
    'recommendations': 'http://127.0.0.1:8005',
    'discounts': 'http://127.0.0.1:8006',
}

# Routes that do not need a token, as (method, path). Every other route needs one.
PUBLIC_ROUTES = {
    ('POST', '/api/v1/login'),
    ('GET', '/api/v1/login/recent-users'),
}

# The login service signs the tokens with HS256 and a secret of at least 32 characters.
# This is used to avoid another token type from being accepted by the Gateway
JWT_ALGORITHM = 'HS256'
JWT_SECRET_MIN_LENGTH = 32

try:
    from .local_settings import JWT_SECRET_KEY
except ImportError:  # no local_settings.py (or no JWT_SECRET_KEY in it)
    JWT_SECRET_KEY = ''


def get_jwt_secret():
    """Return the secret used to check the signature of the tokens.

    # REMINDER FOR THE TEAM: the gateway and the login service must use the SAME secret, each one
    # in its own local_settings.py. If the two values differ, every token is refused (401).

    Returns:
        str: The value of JWT_SECRET_KEY from local_settings.py.

    Raises:
        RuntimeError: If the secret is missing or shorter than 32 characters.
    """
    if len(JWT_SECRET_KEY) < JWT_SECRET_MIN_LENGTH:
        raise RuntimeError(
            'JWT_SECRET_KEY must be in gateway/local_settings.py (at least 32 characters), '
            'with the same value as in the login service.'
        )
    return JWT_SECRET_KEY
