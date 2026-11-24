from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Dashboard, Section
from app.schemas import SectionCreate, SectionOut, SectionUpdate
from app.security import require_role

router = APIRouter(tags=["sections"])


@router.get("/sections", response_model=List[SectionOut])
def list_sections(db: Session = Depends(get_db)):
    return db.query(Section).order_by(Section.id).all()


@router.post("/sections", response_model=SectionOut)
def create_section(
    payload: SectionCreate,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    dashboard = db.get(Dashboard, payload.dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    exists = (
        db.query(Section)
        .filter(Section.dashboard_id == payload.dashboard_id, Section.name == payload.name)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="Section name already exists in this dashboard")

    section = Section(
        dashboard_id=payload.dashboard_id,
        name=payload.name,
        chart_type=payload.chart_type,
        chart_headline=payload.chart_headline,
        chart_change=payload.chart_change,
        chart_labels=payload.chart_labels,
        chart_values=payload.chart_values,
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


@router.patch("/sections/{section_id}", response_model=SectionOut)
def update_section(
    section_id: int,
    payload: SectionUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    section = db.get(Section, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    duplicate = db.query(Section).filter(
        Section.dashboard_id == section.dashboard_id,
        Section.name == payload.name,
        Section.id != section_id,
    ).first()
    if duplicate:
        raise HTTPException(status_code=400, detail="Section name already exists in this dashboard")

    section.name = payload.name
    section.chart_type = payload.chart_type
    section.chart_headline = payload.chart_headline
    section.chart_change = payload.chart_change
    section.chart_labels = payload.chart_labels
    section.chart_values = payload.chart_values
    db.commit()
    db.refresh(section)
    return section


@router.delete("/sections/{section_id}", status_code=204)
def delete_section(
    section_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    section = db.get(Section, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    from app.models import Review
    db.query(Review).filter(Review.section_id == section_id).delete(synchronize_session=False)
    db.delete(section)
    db.commit()
