# app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Any, List
from jose import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from app.core.config import settings

# Configuration Argon2id conforme OWASP
password_hash = PasswordHash((
    Argon2Hasher(
        time_cost=3,          # 3 itérations
        memory_cost=65536,    # 64 MiB RAM
        parallelism=4         # 4 threads
    ),
))

def hash_password(password: str) -> str:
    """Génère une empreinte Argon2id sécurisée avec sel cryptographique unique."""
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie l'authenticité d'un mot de passe contre son empreinte Argon2id."""
    return password_hash.verify(plain_password, hashed_password)

def create_access_token(
    subject: str | Any,
    role: str = "Propriétaire",
    permissions: List[str] | None = None,
    shop_id: str | None = None
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
        "role": role,
        "shop_id": str(shop_id) if shop_id else None,
        "perms": permissions or ["*"]
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(subject: str | Any) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

