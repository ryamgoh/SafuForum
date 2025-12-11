from core.jwt_handler import decode_jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Security

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """A dependency function to verify the token and return user info."""
    token = credentials.credentials
    payload = decode_jwt(token)
    return payload # Returns the user payload if valid, otherwise raises HTTPException