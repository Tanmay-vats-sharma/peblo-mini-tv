from datetime import datetime, timedelta, timezone

import jwt
from pydantic_settings import BaseSettings, SettingsConfigDict
from pwdlib import PasswordHash


class SecuritySettings(BaseSettings):
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


security_settings = SecuritySettings()
password_hash = PasswordHash.recommended()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(subject: str, role: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=security_settings.access_token_expire_minutes
    )
    payload = {
        "sub": subject,
        "role": role,
        "exp": expires_at,
    }
    return jwt.encode(
        payload,
        security_settings.jwt_secret_key,
        algorithm=security_settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        security_settings.jwt_secret_key,
        algorithms=[security_settings.jwt_algorithm],
    )
