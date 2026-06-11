from datetime import datetime, date
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models import (
    Shift, Signup, VolunteerProfile, User, Attendance,
    ShiftStatusEnum, SignupStatusEnum, ShiftTypeEnum,
    TrainingStatusEnum, AttendanceStatusEnum
)
from ..schemas import SignupCreate, ShiftCreate


def check_signup_conflicts(
    db: Session,
    volunteer_id: int,
    shift_id: int,
    exclude_signup_id: Optional[int] = None
) -> Tuple[bool, Optional[str], Optional[Shift]]:
    target_shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not target_shift:
        return True, "班次不存在", None

    approved_signups = db.query(Signup).filter(
        Signup.volunteer_id == volunteer_id,
        Signup.status == SignupStatusEnum.APPROVED,
        Signup.shift_id != shift_id if exclude_signup_id else Signup.shift_id != -1
    ).all()

    for signup in approved_signups:
        other_shift = signup.shift
        if not other_shift:
            continue

        if other_shift.shift_date == target_shift.shift_date:
            if other_shift.study_room_id != target_shift.study_room_id:
                return True, "同日跨点位排班冲突", other_shift

            target_start = datetime.combine(target_shift.shift_date, target_shift.start_time)
            target_end = datetime.combine(target_shift.shift_date, target_shift.end_time)
            other_start = datetime.combine(other_shift.shift_date, other_shift.start_time)
            other_end = datetime.combine(other_shift.shift_date, other_shift.end_time)

            if target_start < other_end and target_end > other_start:
                return True, "同时段班次时间重叠", other_shift

    return False, None, None


def check_night_shift_training(
    db: Session,
    volunteer_id: int,
    shift_id: int
) -> Tuple[bool, Optional[str]]:
    target_shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not target_shift:
        return True, "班次不存在"

    if target_shift.shift_type != ShiftTypeEnum.NIGHT:
        return False, None

    volunteer_profile = db.query(VolunteerProfile).filter(
        VolunteerProfile.user_id == volunteer_id
    ).first()

    if not volunteer_profile or volunteer_profile.training_status != TrainingStatusEnum.COMPLETED:
        return True, "未完成培训的志愿者不能排晚班"

    return False, None


def has_checked_in(db: Session, shift_id: int, volunteer_id: int) -> bool:
    attendance = db.query(Attendance).filter(
        Attendance.shift_id == shift_id,
        Attendance.volunteer_id == volunteer_id,
        Attendance.status.in_([AttendanceStatusEnum.PRESENT, AttendanceStatusEnum.LATE])
    ).first()
    return attendance is not None


def is_shift_full(db: Session, shift_id: int) -> Tuple[bool, Optional[str]]:
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        return True, "班次不存在"
    
    if shift.status == ShiftStatusEnum.CANCELLED:
        return True, "班次已取消"
    
    if shift.status == ShiftStatusEnum.FULL:
        return True, "班次已满员"
    
    if shift.status != ShiftStatusEnum.PUBLISHED:
        return True, "班次未发布，无法报名"

    approved_count = db.query(Signup).filter(
        Signup.shift_id == shift_id,
        Signup.status == SignupStatusEnum.APPROVED
    ).count()

    if approved_count >= shift.max_volunteers:
        return True, "班次已满员"

    return False, None


def get_approved_count(db: Session, shift_id: int) -> int:
    return db.query(Signup).filter(
        Signup.shift_id == shift_id,
        Signup.status == SignupStatusEnum.APPROVED
    ).count()


def update_shift_current_volunteers(db: Session, shift_id: int):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        return

    approved_count = get_approved_count(db, shift_id)
    shift.current_volunteers = approved_count

    if shift.status == ShiftStatusEnum.PUBLISHED:
        if approved_count >= shift.max_volunteers:
            shift.status = ShiftStatusEnum.FULL
    elif shift.status == ShiftStatusEnum.FULL:
        if approved_count < shift.max_volunteers:
            shift.status = ShiftStatusEnum.PUBLISHED

    db.add(shift)
