"""This module handles JWT verification and decoding."""

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from fastapi import HTTPException
from core.config import get_settings

settings = get_settings()
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm

def decode_jwt(token: str):
    """Decodes and validates the JWT."""
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
