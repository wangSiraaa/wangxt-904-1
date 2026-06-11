from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, VolunteerProfile, RoleEnum, AuditLog, TrainingStatusEnum
from ..schemas import (
    VolunteerProfileUpdate, VolunteerDetail,
    VolunteerProfile as VolunteerProfileSchema
)
from ..auth import get_current_user, require_roles

router = APIRouter(prefix="/api/volunteers", tags=["志愿者"])


@router.get("", response_model=List[VolunteerDetail])
def list_volunteers(
    training_status: Optional[TrainingStatusEnum] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(User).filter(User.role == RoleEnum.VOLUNTEER)

    if training_status:
        query = query.join(VolunteerProfile).filter(
            VolunteerProfile.training_status == training_status
        )

    volunteers = query.all()
    return volunteers


@router.get("/{volunteer_id}", response_model=VolunteerDetail)
def get_volunteer(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    volunteer = db.query(User).filter(
        User.id == volunteer_id,
        User.role == RoleEnum.VOLUNTEER
    ).first()

    if not volunteer:
        raise HTTPException(status_code=404, detail="志愿者不存在")

    return volunteer


@router.get("/profile/me", response_model=VolunteerProfileSchema)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(VolunteerProfile).filter(
        VolunteerProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="志愿者档案不存在")

    return profile


@router.put("/profile/{volunteer_id}/training")
def update_training_status(
    volunteer_id: int,
    training_status: TrainingStatusEnum,
    training_date: Optional[str] = None,
    training_teacher: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.TRAINING, RoleEnum.ADMIN))
):
    profile = db.query(VolunteerProfile).filter(
        VolunteerProfile.user_id == volunteer_id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="志愿者档案不存在")

    profile.training_status = training_status
    if training_date:
        from datetime import date
        profile.training_date = date.fromisoformat(training_date)
    if training_teacher:
        profile.training_teacher = training_teacher

    db.add(profile)

    if request:
        audit = AuditLog(
            user_id=current_user.id,
            action="training_update",
            entity_type="volunteer",
            entity_id=volunteer_id,
            details=f"更新培训状态为: {training_status.value}",
            ip_address=request.client.host if request.client else None
        )
        db.add(audit)

    db.commit()
    db.refresh(profile)
    return profile
