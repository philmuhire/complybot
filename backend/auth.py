"""Clerk JWT verification for API routes — keys and JWKS URL come only from environment."""

from typing import Annotated

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from compliance_core.config import get_settings

_bearer = HTTPBearer(auto_error=False)


async def clerk_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> dict:
    settings = get_settings()
    jwks_url = settings.clerk_jwks_url

    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    async with httpx.AsyncClient() as client:
        r = await client.get(jwks_url, timeout=15.0)
        r.raise_for_status()
        jwks = r.json()

    token = creds.credentials
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        key_data = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if not key_data:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown signing key")
        pub = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
        payload = jwt.decode(
            token,
            pub,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {e}") from e
