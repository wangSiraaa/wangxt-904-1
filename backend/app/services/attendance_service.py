from datetime import datetime, time as dt_time
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..models import (
    Attendance, Shift, Signup, AuditLog,
    AttendanceStatusEnum, SignupStatusEnum, ShiftStatusEnum
)


def check_in(
    db: Session,
    shift_id: int,
    volunteer_id: int,
    ip_address: Optional[str] = None
) -> Attendance:
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="班次不存在")

    signup = db.query(Signup).filter(
        Signup.shift_id == shift_id,
        Signup.volunteer_id == volunteer_id,
        Signup.status == SignupStatusEnum.APPROVED
    ).first()

    if not signup:
        raise HTTPException(status_code=400, detail="您没有该班次的报名记录或报名未审核通过")

    attendance = db.query(Attendance).filter(
        Attendance.shift_id == shift_id,
        Attendance.volunteer_id == volunteer_id
    ).first()

    if not attendance:
        attendance = Attendance(
            shift_id=shift_id,
            volunteer_id=volunteer_id,
            status=AttendanceStatusEnum.NOT_CHECKED_IN
        )
        db.add(attendance)
        db.flush()

    if attendance.status in [AttendanceStatusEnum.PRESENT, AttendanceStatusEnum.LATE]:
        return attendance

    now = datetime.utcnow()
    attendance.check_in_time = now

    shift_start = datetime.combine(shift.shift_date, shift.start_time)
    if now > shift_start:
        attendance.status = AttendanceStatusEnum.LATE
    else:
        attendance.status = AttendanceStatusEnum.PRESENT

    db.add(attendance)

    audit_log = AuditLog(
        user_id=volunteer_id,
        action="check_in",
        entity_type="attendance",
        entity_id=attendance.id,
        details=f"签到班次 {shift_id}",
        ip_address=ip_address
    )
    db.add(audit_log)

    db.commit()
    db.refresh(attendance)

    return attendance


def check_out(
    db: Session,
    shift_id: int,
    volunteer_id: int,
    ip_address: Optional[str] = None
) -> Attendance:
    attendance = db.query(Attendance).filter(
        Attendance.shift_id == shift_id,
        Attendance.volunteer_id == volunteer_id
    ).first()

    if not attendance:
        raise HTTPException(status_code=404, detail="未找到签到记录")

    if attendance.status == AttendanceStatusEnum.NOT_CHECKED_IN:
        raise HTTPException(status_code=400, detail="尚未签到，无法签退")

    if attendance.check_out_time:
        return attendance

    now = datetime.utcnow()
    attendance.check_out_time = now

    if attendance.check_in_time:
        duration = (now - attendance.check_in_time).total_seconds() / 3600.0
        attendance.duration_hours = round(duration, 2)

    db.add(attendance)

    audit_log = AuditLog(
        user_id=volunteer_id,
        action="check_out",
        entity_type="attendance",
        entity_id=attendance.id,
        details=f"签退班次 {shift_id}",
        ip_address=ip_address
    )
    db.add(audit_log)

    db.commit()
    db.refresh(attendance)

    return attendance


def get_attendance_by_shift(db: Session, shift_id: int):
    return db.query(Attendance).filter(Attendance.shift_id == shift_id).all()


def get_attendance_by_volunteer(db: Session, volunteer_id: int):
    return db.query(Attendance).filter(Attendance.volunteer_id == volunteer_id).all()
