import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Dashboard, ShareLink
from app.schemas import ShareLinkCreate, ShareLinkOut, SharedDashboardOut
from app.security import require_role

router = APIRouter(tags=["sharing"])


@router.post("/dashboards/{dashboard_id}/share", response_model=ShareLinkOut)
def create_share_link(
    dashboard_id: int,
    payload: ShareLinkCreate,
    db: Session = Depends(get_db),
    _=Depends(require_role("analyst", "admin")),
):
    dashboard = db.get(Dashboard, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    share_link = ShareLink(
        dashboard_id=dashboard_id,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=payload.expires_in_hours),
    )
    db.add(share_link)
    db.commit()
    db.refresh(share_link)
    return share_link


@router.get("/api/shared/{token}", response_model=SharedDashboardOut)
def get_shared_dashboard(token: str, db: Session = Depends(get_db)):
    share_link = db.query(ShareLink).filter(ShareLink.token == token).first()
    if not share_link:
        raise HTTPException(status_code=404, detail="Share link not found")

    expires_at = share_link.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Share link has expired")

    dashboard = db.get(Dashboard, share_link.dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    return dashboard
