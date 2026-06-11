from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, RoleEnum, Signup, Shift
from ..schemas import (
    SignupCreate, SignupUpdate, Signup as SignupSchema,
    SignupWithDetails
)
from ..auth import get_current_user, require_roles
from ..services import signup_service as ss
from ..services.shift_service import check_signup_conflicts, check_night_shift_training

router = APIRouter(prefix="/api/signups", tags=["报名"])


@router.get("", response_model=List[SignupWithDetails])
def list_signups(
    shift_id: Optional[int] = None,
    volunteer_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Signup)

    if current_user.role == RoleEnum.VOLUNTEER:
        query = query.filter(Signup.volunteer_id == current_user.id)
    elif volunteer_id:
        query = query.filter(Signup.volunteer_id == volunteer_id)

    if shift_id:
        query = query.filter(Signup.shift_id == shift_id)
    if status:
        query = query.filter(Signup.status == status)

    return query.order_by(Signup.created_at.desc()).all()


@router.get("/{signup_id}", response_model=SignupWithDetails)
def get_signup(
    signup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    signup = db.query(Signup).filter(Signup.id == signup_id).first()
    if not signup:
        raise HTTPException(status_code=404, detail="报名记录不存在")

    if current_user.role == RoleEnum.VOLUNTEER and signup.volunteer_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看他人报名记录")

    return signup


@router.post("", response_model=SignupSchema)
def create_signup(
    signup_data: SignupCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.VOLUNTEER, RoleEnum.ADMIN))
):
    ip = request.client.host if request.client else None
    volunteer_id = current_user.id
    return ss.create_signup(db, volunteer_id, signup_data, ip)


@router.put("/{signup_id}/approve", response_model=SignupSchema)
def approve_signup(
    signup_id: int,
    request: Request,
    review_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.OPERATIONS))
):
    ip = request.client.host if request.client else None
    return ss.approve_signup(db, signup_id, current_user.id, review_notes, ip)


@router.put("/{signup_id}/reject", response_model=SignupSchema)
def reject_signup(
    signup_id: int,
    request: Request,
    review_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.OPERATIONS))
):
    ip = request.client.host if request.client else None
    return ss.reject_signup(db, signup_id, current_user.id, review_notes, ip)


@router.delete("/{signup_id}")
def cancel_signup(
    signup_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ip = request.client.host if request.client else None
    is_admin = current_user.role in [RoleEnum.ADMIN, RoleEnum.OPERATIONS]
    ss.cancel_signup(db, signup_id, current_user.id, is_admin, ip)
    return {"message": "取消报名成功"}


@router.get("/check/conflict")
def check_conflict(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    has_conflict, conflict_msg, conflict_shift = check_signup_conflicts(
        db, current_user.id, shift_id
    )
    night_issue, night_msg = check_night_shift_training(
        db, current_user.id, shift_id
    )

    conflicts = []
    if has_conflict:
        conflicts.append({
            "type": "time_conflict",
            "message": conflict_msg,
            "conflicting_shift_id": conflict_shift.id if conflict_shift else None
        })
    if night_issue:
        conflicts.append({
            "type": "training_required",
            "message": night_msg
        })

    return {
        "has_conflict": len(conflicts) > 0,
        "conflicts": conflicts
    }
