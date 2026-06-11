from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, RoleEnum, DuplicateCheck, DuplicateCheckTypeEnum
from ..schemas import (
    DuplicateCheck as DuplicateCheckSchema,
    DuplicateCheckWithDetails,
    DuplicateCheckResult
)
from ..auth import get_current_user, require_roles
from ..services import duplicate_check_service as dcs

router = APIRouter(prefix="/api/duplicate-checks", tags=["重复校验"])


@router.get("", response_model=List[DuplicateCheckWithDetails])
def list_duplicate_checks(
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    volunteer_id: Optional[int] = None,
    shift_id: Optional[int] = None,
    check_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == RoleEnum.VOLUNTEER and volunteer_id and volunteer_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看他人校验记录")

    if current_user.role == RoleEnum.VOLUNTEER:
        volunteer_id = current_user.id

    return dcs.get_duplicate_checks(
        db, entity_type, entity_id, volunteer_id, shift_id,
        check_type, status, limit, offset
    )


@router.get("/timeline")
def get_timeline(
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    volunteer_id: Optional[int] = None,
    shift_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == RoleEnum.VOLUNTEER and volunteer_id and volunteer_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看他人校验记录")

    if current_user.role == RoleEnum.VOLUNTEER:
        volunteer_id = current_user.id

    timeline = dcs.get_duplicate_check_timeline(
        db, entity_type, entity_id, volunteer_id, shift_id, days
    )
    return {
        "total": len(timeline),
        "timeline": timeline
    }


@router.get("/{check_id}", response_model=DuplicateCheckWithDetails)
def get_duplicate_check(
    check_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check = db.query(DuplicateCheck).filter(DuplicateCheck.id == check_id).first()
    if not check:
        raise HTTPException(status_code=404, detail="校验记录不存在")

    if current_user.role == RoleEnum.VOLUNTEER and check.volunteer_id and check.volunteer_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看他人校验记录")

    return check


@router.post("/check/signup")
def check_signup_duplicate(
    shift_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    volunteer_id = current_user.id

    checks = dcs.perform_full_signup_check(
        db, volunteer_id, shift_id, current_user.id
    )

    has_duplicate = any(
        c.status.value in ["fail", "warning"] for c in checks
    )

    conflicts = []
    for check in checks:
        if check.status.value in ["fail", "warning"]:
            conflicts.append({
                "check_id": check.id,
                "check_type": check.check_type.value,
                "status": check.status.value,
                "message": check.check_reason,
                "conflict_details": check.conflict_details,
                "conflicting_entity_id": check.conflict_entity_id,
                "check_time": check.check_time
            })

    return {
        "has_duplicate": has_duplicate,
        "total_checks": len(checks),
        "conflicts": conflicts,
        "all_checks": [
            {
                "id": c.id,
                "check_type": c.check_type.value,
                "status": c.status.value,
                "check_reason": c.check_reason,
                "check_time": c.check_time
            }
            for c in checks
        ]
    }


@router.post("/check/shift")
def check_shift_duplicate(
    study_room_id: int,
    shift_date: str,
    start_time: str,
    end_time: str,
    exclude_shift_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.OPERATIONS))
):
    from datetime import datetime, date, time as dt_time

    try:
        shift_date_obj = datetime.strptime(shift_date, "%Y-%m-%d").date()
        start_time_obj = datetime.strptime(start_time, "%H:%M:%S").time()
        end_time_obj = datetime.strptime(end_time, "%H:%M:%S").time()
    except ValueError:
        raise HTTPException(status_code=400, detail="日期时间格式错误")

    has_dup, check_record, conflict_shift = dcs.check_shift_duplicate(
        db, study_room_id, shift_date_obj, start_time_obj, end_time_obj,
        exclude_shift_id, current_user.id
    )
    db.commit()

    return {
        "has_duplicate": has_dup,
        "check_id": check_record.id if check_record else None,
        "check_type": check_record.check_type.value if check_record else None,
        "status": check_record.status.value if check_record else None,
        "message": check_record.check_reason if check_record else None,
        "conflict_details": check_record.conflict_details if check_record else None,
        "conflicting_shift_id": conflict_shift.id if conflict_shift else None,
        "conflicting_shift": {
            "id": conflict_shift.id,
            "study_room_name": conflict_shift.study_room.name if conflict_shift and conflict_shift.study_room else None,
            "start_time": str(conflict_shift.start_time) if conflict_shift else None,
            "end_time": str(conflict_shift.end_time) if conflict_shift else None,
            "shift_type": conflict_shift.shift_type.value if conflict_shift else None,
        } if conflict_shift else None
    }


@router.post("/check/attendance")
def check_attendance_duplicate(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    volunteer_id = current_user.id

    has_dup, check_record, conflict_attendance = dcs.check_attendance_duplicate(
        db, volunteer_id, shift_id, current_user.id
    )
    db.commit()

    return {
        "has_duplicate": has_dup,
        "check_id": check_record.id if check_record else None,
        "check_type": check_record.check_type.value if check_record else None,
        "status": check_record.status.value if check_record else None,
        "message": check_record.check_reason if check_record else None,
        "conflict_details": check_record.conflict_details if check_record else None,
        "conflicting_attendance_id": conflict_attendance.id if conflict_attendance else None
    }


@router.post("/check/study-room")
def check_study_room_duplicate(
    name: str,
    address: str = None,
    exclude_room_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.OPERATIONS))
):
    checks = dcs.perform_full_study_room_check(
        db, name, address, exclude_room_id, current_user.id
    )

    has_duplicate = any(
        c.status.value in ["fail", "warning"] for c in checks
    )

    conflicts = []
    for check in checks:
        if check.status.value in ["fail", "warning"]:
            conflicts.append({
                "check_id": check.id,
                "check_type": check.check_type.value,
                "status": check.status.value,
                "message": check.check_reason,
                "conflict_details": check.conflict_details,
                "conflicting_entity_id": check.conflict_entity_id,
                "conflict_study_room_id": check.study_room_id,
                "check_time": check.check_time
            })

    return {
        "has_duplicate": has_duplicate,
        "total_checks": len(checks),
        "conflicts": conflicts,
        "all_checks": [
            {
                "id": c.id,
                "check_type": c.check_type.value,
                "status": c.status.value,
                "check_reason": c.check_reason,
                "check_time": c.check_time
            }
            for c in checks
        ]
    }
