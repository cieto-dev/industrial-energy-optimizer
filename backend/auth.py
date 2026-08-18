"""
Authentication utilities.

Provides:
- password hashing / verification (bcrypt via passlib)
- JWT access token creation
- JWT access token verification (as a FastAPI dependency)

Does NOT contain:
- user storage (see models / database layer)
- login route (see apis/auth_api.py)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from config import settings


# --------------------------------------------------
# Password hashing
# --------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password for storage. Never store plain passwords."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain-text password against a stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# --------------------------------------------------
# JWT configuration
# --------------------------------------------------

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a signed JWT containing the given claims.

    `data` should include at least a "sub" (subject) claim identifying
    the user, e.g. {"sub": user.email}.
    """

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


# --------------------------------------------------
# Token verification (FastAPI dependency)
# --------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    FastAPI dependency: verifies the bearer token on a request and
    returns the subject (user identifier) it was issued for.

    Raises 401 if the token is missing, invalid, or expired.

    Usage on a protected route:
        @router.get("/something")
        def read_something(current_user: str = Depends(get_current_user)):
            ...
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        subject: Optional[str] = payload.get("sub")

        if subject is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    return subject