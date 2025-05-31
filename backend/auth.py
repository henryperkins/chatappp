# Authentication and session management
import bcrypt
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, Request, Response, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import settings
from .models import LoginRequest
import time

# Rate limiting storage
login_attempts: Dict[str, list] = {}


class AuthManager:
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"
        self.pwd_context = bcrypt

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hashpw(
            password.encode("utf-8"), self.pwd_context.gensalt()
        ).decode("utf-8")

    def create_session_token(self, username: str) -> str:
        expire = datetime.utcnow() + timedelta(minutes=settings.session_expire_minutes)
        data = {"sub": username, "exp": expire, "csrf": secrets.token_urlsafe(32)}
        return jwt.encode(data, self.secret_key, algorithm=self.algorithm)

    def verify_session_token(self, token: str) -> Optional[Dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def check_rate_limit(self, identifier: str) -> bool:
        current_time = time.time()
        if identifier not in login_attempts:
            login_attempts[identifier] = []

        # Clean old attempts
        login_attempts[identifier] = [
            attempt
            for attempt in login_attempts[identifier]
            if current_time - attempt < 60
        ]

        # Check if exceeded limit
        if len(login_attempts[identifier]) >= 5:
            return False

        login_attempts[identifier].append(current_time)
        return True


auth_manager = AuthManager()


def get_current_user(request: Request) -> str:
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = auth_manager.verify_session_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return payload["sub"]


def verify_csrf_token(request: Request, token: str) -> bool:
    session_token = request.cookies.get("session_token")
    if not session_token:
        return False

    payload = auth_manager.verify_session_token(session_token)
    if not payload:
        return False

    return payload.get("csrf") == token
