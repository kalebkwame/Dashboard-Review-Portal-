import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AdminInvitation, Dashboard, PasswordReset, User
from app.schemas import AdminBootstrap, AdminInvitationCreate, AdminInvitationOut, AdminInvitationRedeem, PasswordResetRedeem, PasswordResetRequest, PasswordResetOut, TokenOut, UserCreate, UserLogin, UserOut, UserRoleUpdate
from app.security import create_access_token, get_current_user, get_password_hash, require_role, verify_password
from app.email import send_admin_invitation, send_password_reset

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        role="viewer",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(subject=user.email, role=user.role)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/users", response_model=list[UserOut])
def list_users(_=Depends(require_role("admin")), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


@router.patch("/users/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Use a separate account to change your own role")

    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@router.post("/bootstrap-admin", response_model=UserOut, status_code=201)
def bootstrap_admin(payload: AdminBootstrap, db: Session = Depends(get_db)):
    existing_admin = db.query(User).filter(User.role == "admin").first()
    if existing_admin:
        raise HTTPException(status_code=403, detail="An admin account already exists")

    setup_key = os.getenv("ADMIN_SETUP_KEY")
    if not setup_key:
        raise HTTPException(status_code=503, detail="Admin setup is not configured")
    if not secrets.compare_digest(payload.setup_key, setup_key):
        raise HTTPException(status_code=403, detail="Invalid admin setup key")

    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    admin = User(
        name=payload.name,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        role="admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reassignment_owner = db.query(User).filter(User.id != user.id).first()
    if reassignment_owner:
        db.query(Dashboard).filter(Dashboard.owner_id == user.id).update(
            {Dashboard.owner_id: reassignment_owner.id}, synchronize_session=False
        )

    db.delete(user)
    db.commit()


@router.post("/admin-invitations", response_model=AdminInvitationOut)
def create_admin_invitation(
    payload: AdminInvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    token = secrets.token_urlsafe(32)
    invitation = AdminInvitation(
        email=payload.email,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        created_by_id=current_user.id,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    origin = os.getenv("APP_ORIGIN", "http://127.0.0.1:8001")
    send_admin_invitation(invitation.email, f"{origin.rstrip('/')}/admin/invite/{invitation.token}")
    return invitation


@router.get("/admin-invitations/{token}")
def get_admin_invitation(token: str, db: Session = Depends(get_db)):
    invitation = db.query(AdminInvitation).filter(AdminInvitation.token == token).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invitation.used_at is not None:
        raise HTTPException(status_code=410, detail="Invitation already used")

    expires_at = invitation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Invitation expired")

    return {"email": invitation.email, "expires_at": invitation.expires_at}


@router.post("/admin-invitations/{token}/redeem", response_model=UserOut, status_code=201)
def redeem_admin_invitation(
    token: str,
    payload: AdminInvitationRedeem,
    db: Session = Depends(get_db),
):
    invitation = db.query(AdminInvitation).filter(AdminInvitation.token == token).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invitation.used_at is not None:
        raise HTTPException(status_code=410, detail="Invitation already used")

    expires_at = invitation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Invitation expired")

    existing = db.query(User).filter(User.email == invitation.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    admin = User(
        name=payload.name,
        email=invitation.email,
        password_hash=get_password_hash(payload.password),
        role="admin",
    )
    db.add(admin)
    db.flush()
    invitation.used_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(admin)
    return admin


@router.post("/password-reset/request", response_model=PasswordResetOut | None)
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        return None

    token = secrets.token_urlsafe(32)
    reset = PasswordReset(
        user_id=user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(reset)
    db.commit()
    db.refresh(reset)
    origin = os.getenv("APP_ORIGIN", "http://127.0.0.1:8001")
    send_password_reset(user.email, f"{origin.rstrip('/')}/reset-password/{reset.token}")
    return reset


@router.post("/password-reset/{token}")
def redeem_password_reset(
    token: str,
    payload: PasswordResetRedeem,
    db: Session = Depends(get_db),
):
    reset = db.query(PasswordReset).filter(PasswordReset.token == token).first()
    if not reset:
        raise HTTPException(status_code=404, detail="Reset link not found")
    if reset.used_at is not None:
        raise HTTPException(status_code=410, detail="Reset link already used")

    expires_at = reset.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Reset link expired")

    user = db.get(User, reset.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = get_password_hash(payload.password)
    reset.used_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Password updated"}
