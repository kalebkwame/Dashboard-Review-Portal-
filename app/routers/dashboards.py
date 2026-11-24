from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Dashboard, Section, ShareLink, User
from app.schemas import DashboardCreate, DashboardOut
from app.security import require_role

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@router.get("", response_model=List[DashboardOut])
def list_dashboards(db: Session = Depends(get_db)):
    return db.query(Dashboard).order_by(Dashboard.id).all()


@router.get("/{dashboard_id}", response_model=DashboardOut)
def get_dashboard(dashboard_id: int, db: Session = Depends(get_db)):
    dashboard = db.get(Dashboard, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.post("", response_model=DashboardOut)
def create_dashboard(
    payload: DashboardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("analyst", "admin")),
):
    exists = db.query(Dashboard).filter(Dashboard.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Dashboard name already exists")

    dashboard = Dashboard(
        name=payload.name,
        description=payload.description,
        owner_id=current_user.id,
    )
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)
    return dashboard


@router.delete("/{dashboard_id}", status_code=204)
def delete_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    dashboard = db.get(Dashboard, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    for section in db.query(Section).filter(Section.dashboard_id == dashboard_id).all():
        from app.models import Review
        db.query(Review).filter(Review.section_id == section.id).delete(synchronize_session=False)
        db.delete(section)

    db.query(ShareLink).filter(ShareLink.dashboard_id == dashboard_id).delete(synchronize_session=False)
    db.delete(dashboard)
    db.commit()
