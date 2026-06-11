from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, RoleEnum
from ..schemas import Attendance as AttendanceSchema, AttendanceWithDetails
from ..auth import get_current_user, require_roles
from ..services import attendance_service as ats

router = APIRouter(prefix="/api/attendance", tags=["签到签退"])


@router.get("")
def list_attendances(
    shift_id: Optional[int] = None,
    volunteer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if shift_id:
        return ats.get_attendance_by_shift(db, shift_id)
    if volunteer_id:
        if current_user.role == RoleEnum.VOLUNTEER and volunteer_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权查看他人签到记录")
        return ats.get_attendance_by_volunteer(db, volunteer_id)
    if current_user.role == RoleEnum.VOLUNTEER:
        return ats.get_attendance_by_volunteer(db, current_user.id)
    return []


@router.get("/shift/{shift_id}", response_model=List[AttendanceWithDetails])
def get_shift_attendances(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ats.get_attendance_by_shift(db, shift_id)


@router.post("/check-in", response_model=AttendanceSchema)
def check_in(
    shift_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.VOLUNTEER, RoleEnum.ADMIN))
):
    ip = request.client.host if request.client else None
    volunteer_id = current_user.id
    return ats.check_in(db, shift_id, volunteer_id, ip)


@router.post("/check-out", response_model=AttendanceSchema)
def check_out(
    shift_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.VOLUNTEER, RoleEnum.ADMIN))
):
    ip = request.client.host if request.client else None
    volunteer_id = current_user.id
    return ats.check_out(db, shift_id, volunteer_id, ip)


@router.get("/my")
def get_my_attendances(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ats.get_attendance_by_volunteer(db, current_user.id)
