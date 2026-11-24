from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Review, Section, User
from app.schemas import ReviewCreate, ReviewOut, ReviewStatusUpdate
from app.security import require_role

router = APIRouter(tags=["reviews"])


@router.get("/sections/{section_id}/reviews", response_model=List[ReviewOut])
def list_reviews(section_id: int, db: Session = Depends(get_db)):
    section = db.get(Section, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    return (
        db.query(Review)
        .filter(Review.section_id == section_id)
        .order_by(Review.id.desc())
        .all()
    )


@router.post("/sections/{section_id}/reviews", response_model=ReviewOut)
def create_review(
    section_id: int,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("viewer", "analyst", "admin")),
):
    section = db.get(Section, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    review = Review(
        section_id=section_id,
        reviewer_name=payload.reviewer_name,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.patch("/reviews/{review_id}/status", response_model=ReviewOut)
def update_review_status(
    review_id: int,
    payload: ReviewStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.status = payload.status
    db.commit()
    db.refresh(review)
    return review
