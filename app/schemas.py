from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ReviewStatus = Literal["open", "in_progress", "resolved"]
UserRole = Literal["viewer", "analyst", "admin"]


class DashboardCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=1000)


class DashboardOut(BaseModel):
    id: int
    name: str
    description: str
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SectionCreate(BaseModel):
    dashboard_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=100)
    chart_type: str = Field(default="bar", min_length=3, max_length=50)
    chart_headline: str = Field(default="", max_length=100)
    chart_change: str = Field(default="", max_length=200)
    chart_labels: list[str] = Field(default_factory=list)
    chart_values: list[float] = Field(default_factory=list)


class SectionOut(BaseModel):
    id: int
    dashboard_id: int
    name: str
    chart_type: str
    chart_headline: str
    chart_change: str
    chart_labels: list[str]
    chart_values: list[float]

    model_config = ConfigDict(from_attributes=True)


class ReviewCreate(BaseModel):
    reviewer_name: str = Field(min_length=2, max_length=100)
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=3, max_length=1000)


class ReviewOut(BaseModel):
    id: int
    section_id: int
    reviewer_name: str
    rating: int
    comment: str
    status: ReviewStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewStatusUpdate(BaseModel):
    status: ReviewStatus


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = "viewer"


class UserLogin(BaseModel):
    email: str
    password: str


class AdminBootstrap(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    setup_key: str = Field(min_length=1, max_length=255)


class UserRoleUpdate(BaseModel):
    role: UserRole


class AdminInvitationCreate(BaseModel):
    email: str = Field(min_length=5, max_length=255)


class AdminInvitationOut(BaseModel):
    email: str
    token: str
    expires_at: datetime


class AdminInvitationRedeem(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class PasswordResetRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)


class PasswordResetOut(BaseModel):
    token: str
    expires_at: datetime


class PasswordResetRedeem(BaseModel):
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    access_token: str
    token_type: str


class ShareLinkCreate(BaseModel):
    expires_in_hours: int = Field(default=24, ge=1, le=720)


class ShareLinkOut(BaseModel):
    token: str
    dashboard_id: int
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SharedSectionOut(BaseModel):
    id: int
    name: str
    chart_type: str
    chart_headline: str
    chart_change: str
    chart_labels: list[str]
    chart_values: list[float]

    model_config = ConfigDict(from_attributes=True)


class SharedDashboardOut(BaseModel):
    name: str
    description: str
    sections: list[SharedSectionOut]

    model_config = ConfigDict(from_attributes=True)


class SectionUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    chart_type: str = Field(min_length=3, max_length=50)
    chart_headline: str = Field(default="", max_length=100)
    chart_change: str = Field(default="", max_length=200)
    chart_labels: list[str] = Field(default_factory=list)
    chart_values: list[float] = Field(default_factory=list)
