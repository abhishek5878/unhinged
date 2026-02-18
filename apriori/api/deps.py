"""FastAPI dependencies for authentication via Clerk JWT verification."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from apriori.config import settings

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)

# Cache the JWKS client (it handles its own key caching internally)
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        jwks_url = f"{settings.clerk_issuer}/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
    return _jwks_client


@dataclass
class ClerkUser:
    """Decoded Clerk JWT claims."""

    user_id: str  # Clerk sub claim
    email: str | None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> ClerkUser:
    """Verify Clerk JWT and return decoded user claims.

    Raises 401 if the token is missing or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
        )

    token = credentials.credentials

    try:
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.clerk_issuer,
            options={"verify_aud": False},
        )

        return ClerkUser(
            user_id=payload["sub"],
            email=payload.get("email"),
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as exc:
        logger.warning("Invalid Clerk JWT: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
