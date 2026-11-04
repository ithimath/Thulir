import os
import time
from collections import defaultdict
from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.models import User, UserSchoolRole, School
from backend.app.services.security import decode_access_token

# In-memory sliding rate limiter for login
LOGIN_ATTEMPTS = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 10
WINDOW_SECONDS = 60

def rate_limit_login(request: Request):
    import os
    if os.getenv("PYTEST_CURRENT_TEST") or settings.APP_ENV == "testing":
        return

    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    # Filter attempts within window
    LOGIN_ATTEMPTS[client_ip] = [ts for ts in LOGIN_ATTEMPTS[client_ip] if now - ts < WINDOW_SECONDS]
    if len(LOGIN_ATTEMPTS[client_ip]) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many sign in attempts. Please wait a minute before trying again.",
        )
    LOGIN_ATTEMPTS[client_ip].append(now)

class AuthenticatedUser:
    def __init__(self, user: User, role: UserSchoolRole, school: School):
        self.user = user
        self.role = role
        self.school = school

    @property
    def id(self) -> int:
        return self.user.id

    @property
    def role_name(self) -> str:
        return self.role.role

    @property
    def school_id(self) -> int:
        return self.school.id

    @property
    def assigned_classes_list(self) -> list[str]:
        if not self.role.assigned_classes:
            return []
        return [c.strip() for c in self.role.assigned_classes.split(",") if c.strip()]


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    # 1. Check Authorization header first (explicit bearer token takes precedence)
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    # 2. Check HttpOnly cookie fallback (browser session)
    if not token:
        token = request.cookies.get("thulir_session")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in.",
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please sign in again.",
        )

    user_id = int(payload["sub"])
    school_id = payload.get("school_id")
    role_name = payload.get("role")

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or deactivated.",
        )

    # Query role for this school
    role_query = db.query(UserSchoolRole).filter(UserSchoolRole.user_id == user.id)
    if school_id:
        role_query = role_query.filter(UserSchoolRole.school_id == school_id)
    if role_name:
        role_query = role_query.filter(UserSchoolRole.role == role_name)

    role = role_query.first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No authorized school role assigned for this account.",
        )

    school = db.query(School).filter(School.id == role.school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found.",
        )

    return AuthenticatedUser(user=user, role=role, school=school)


def require_role(allowed_roles: list[str]):
    def role_checker(auth: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if auth.role_name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}.",
            )
        return auth
    return role_checker

