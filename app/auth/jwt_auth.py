from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from core.config import settings
from core.database import get_db
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import DecodeError, InvalidSignatureError
from sqlalchemy.orm import Session
from users.models import UserModel

security = HTTPBearer()
DB_SESSION = Depends(get_db)


def get_authenticated_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Session = DB_SESSION,
):

    try:
        token = credentials.credentials
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms="HS256")
        user_id = decoded.get("user_id", None)
        token_type = decoded.get("type", None)
        exp_time = datetime.fromtimestamp(decoded.get("exp", None))
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="user_id not in the payload",
            )

        if token_type != "access":
            raise HTTPException(
                status_code=401,
                detail="token type is not valid",
            )

        if datetime.now() > exp_time:
            raise HTTPException(
                status_code=401,
                detail="token is expired",
            )

        user_obj = db.query(UserModel).filter(UserModel.id == user_id).one()
        return user_obj

    except InvalidSignatureError:
        raise HTTPException(status_code=401, detail="invalid signature")

    except DecodeError:
        raise HTTPException(status_code=401, detail="invalid decode")

    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=401, detail=f"Authentication failed, {e}")


def generate_access_token(user_id: int, expires_in: int = 3600 * 24) -> str:
    now = datetime.now(timezone.utc)  # noqa: UP017
    payload = {
        "type": "access",
        "user_id": user_id,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


def generate_refresh_token(user_id: int, expires_in: int = 3600 * 24 * 7) -> str:
    now = datetime.now(timezone.utc)  # noqa: UP017
    payload = {
        "type": "refresh",
        "user_id": user_id,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


def decode_refresh_token(token):
    try:
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms="HS256")
        user_id = decoded.get("user_id", None)
        token_type = decoded.get("type", None)
        exp_time = datetime.fromtimestamp(decoded.get("exp", None))
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="user_id not in the payload",
            )

        if token_type != "refresh":
            raise HTTPException(
                status_code=401,
                detail="token type is not valid",
            )

        if datetime.now() > exp_time:
            raise HTTPException(
                status_code=401,
                detail="token is expired",
            )

        return user_id

    except InvalidSignatureError:
        raise HTTPException(status_code=401, detail="invalid signature")

    except DecodeError:
        raise HTTPException(status_code=401, detail="invalid decode")

    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=401, detail=f"Authentication failed, {e}")
