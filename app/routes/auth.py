from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from firebase_admin import auth as firebase_auth

from app.db.session import get_db
from app.models.models import users, AuthProviderEnum, UserAuthProviders

router = APIRouter(prefix="/auth", tags=["Auth"])
security = HTTPBearer()


def verify_firebase_token(token: str):
    try:
        return firebase_auth.verify_id_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token",
        )


@router.post("/register")
def register_user(data: dict = Body(...),credentials=Depends(security),db: Session = Depends(get_db)):
    token = credentials.credentials
    decoded = verify_firebase_token(token)

    firebase_uid = decoded["uid"]
    email = decoded.get("email")
    email_verified = decoded.get("email_verified", False)

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Email not found in Firebase token",)

    raw_provider = decoded.get("firebase", {}).get("sign_in_provider", "password")
    if raw_provider == "google.com":
        provider_enum = AuthProviderEnum.google
    else:
        provider_enum = AuthProviderEnum.password

    full_name = None

    if provider_enum == AuthProviderEnum.password:
        # For email/password, expect full_name or (first+last) from body
        full_name = data.get("full_name")

        if not full_name:
            first_name = data.get("first_name")
            last_name = data.get("last_name")
            if first_name and last_name:
                full_name = f"{first_name} {last_name}"

        if not full_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="full_name or (first_name + last_name) is required for email/password signup",
            )

    else:
        full_name = decoded.get("name") or decoded.get("display_name")

        # optional: allow override from body if provided
        if data.get("full_name"):
            full_name = data["full_name"]

    user = db.query(users).filter(users.firebase_uid == firebase_uid).first()

    if not user:
        user = users(
            firebase_uid=firebase_uid,
            email=email,
            full_name=full_name,
            is_verified=email_verified,
            auth_provider=provider_enum,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        updated = False

        if not user.full_name and full_name:
            user.full_name = full_name
            updated = True

        if email_verified and not user.is_verified:
            user.is_verified = True
            updated = True

        if user.auth_provider != provider_enum:
            user.auth_provider = provider_enum
            updated = True

        if updated:
            db.commit()
            db.refresh(user)

    # ---- Ensure provider entry exists ----
    provider_row = (
        db.query(UserAuthProviders)
        .filter(
            UserAuthProviders.user_id == user.id,
            UserAuthProviders.provider == provider_enum
        )
        .first()
    )

    if not provider_row:
        provider_row = UserAuthProviders(
            user_id=user.id,
            provider=provider_enum,
            provider_uid=firebase_uid,
        )
        db.add(provider_row)
        db.commit()

    return {
        "message": "User registered successfully",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "provider": provider_enum.value,
        },
    }
