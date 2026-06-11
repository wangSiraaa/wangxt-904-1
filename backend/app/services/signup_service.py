from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models import (
    Shift, Signup, VolunteerProfile, User, Attendance, LeaveRequest,
    ReplacementTodo, AuditLog,
    ShiftStatusEnum, SignupStatusEnum, ShiftTypeEnum,
    TrainingStatusEnum, AttendanceStatusEnum, LeaveStatusEnum,
    ReplacementTodoStatusEnum
)
from ..schemas import SignupCreate, SignupUpdate
from .shift_service import (
    check_signup_conflicts, check_night_shift_training,
    is_shift_full, has_checked_in, update_shift_current_volunteers,
    get_approved_count
)


def create_signup(
    db: Session,
    volunteer_id: int,
    signup_data: SignupCreate,
    ip_address: Optional[str] = None
) -> Signup:
    shift = db.query(Shift).filter(Shift.id == signup_data.shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="班次不存在")

    existing_signup = db.query(Signup).filter(
        Signup.shift_id == signup_data.shift_id,
        Signup.volunteer_id == volunteer_id,
        Signup.status.in_([SignupStatusEnum.PENDING, SignupStatusEnum.APPROVED])
    ).first()

    if existing_signup:
        return existing_signup

    full, full_msg = is_shift_full(db, signup_data.shift_id)
    if full:
        raise HTTPException(status_code=400, detail=full_msg)

    has_conflict, conflict_msg, conflict_shift = check_signup_conflicts(
        db, volunteer_id, signup_data.shift_id
    )
    if has_conflict:
        raise HTTPException(
            status_code=400,
            detail=f"排班冲突: {conflict_msg}（冲突班次: {conflict_shift.id if conflict_shift else '未知'}）"
        )

    night_issue, night_msg = check_night_shift_training(db, volunteer_id, signup_data.shift_id)
    if night_issue:
        raise HTTPException(status_code=400, detail=night_msg)

    new_signup = Signup(
        shift_id=signup_data.shift_id,
        volunteer_id=volunteer_id,
        status=SignupStatusEnum.PENDING,
        signup_time=datetime.utcnow()
    )

    db.add(new_signup)
    db.flush()

    audit_log = AuditLog(
        user_id=volunteer_id,
        action="signup_create",
        entity_type="signup",
        entity_id=new_signup.id,
        details=f"志愿者报名班次 {signup_data.shift_id}",
        ip_address=ip_address
    )
    db.add(audit_log)

    db.commit()
    db.refresh(new_signup)

    return new_signup


def approve_signup(
    db: Session,
    signup_id: int,
    reviewer_id: int,
    review_notes: Optional[str] = None,
    ip_address: Optional[str] = None
) -> Signup:
    signup = db.query(Signup).filter(Signup.id == signup_id).first()
    if not signup:
        raise HTTPException(status_code=404, detail="报名记录不存在")

    if signup.status != SignupStatusEnum.PENDING:
        raise HTTPException(status_code=400, detail="只有待审核的报名可以审批")

    full, full_msg = is_shift_full(db, signup.shift_id)
    if full:
        raise HTTPException(status_code=400, detail="班次已满员，无法审核通过")

    has_conflict, conflict_msg, conflict_shift = check_signup_conflicts(
        db, signup.volunteer_id, signup.shift_id, exclude_signup_id=signup_id
    )
    if has_conflict:
        raise HTTPException(
            status_code=400,
            detail=f"排班冲突: {conflict_msg}"
        )

    night_issue, night_msg = check_night_shift_training(
        db, signup.volunteer_id, signup.shift_id
    )
    if night_issue:
        raise HTTPException(status_code=400, detail=night_msg)

    signup.status = SignupStatusEnum.APPROVED
    signup.review_time = datetime.utcnow()
    signup.reviewed_by = reviewer_id
    signup.review_notes = review_notes

    db.add(signup)
    db.flush()
    update_shift_current_volunteers(db, signup.shift_id)

    attendance = db.query(Attendance).filter(
        Attendance.shift_id == signup.shift_id,
        Attendance.volunteer_id == signup.volunteer_id
    ).first()

    if not attendance:
        attendance = Attendance(
            shift_id=signup.shift_id,
            volunteer_id=signup.volunteer_id,
            status=AttendanceStatusEnum.NOT_CHECKED_IN
        )
        db.add(attendance)

    audit_log = AuditLog(
        user_id=reviewer_id,
        action="signup_approve",
        entity_type="signup",
        entity_id=signup_id,
        details=f"审核通过报名 {signup_id}",
        ip_address=ip_address
    )
    db.add(audit_log)

    db.commit()
    db.refresh(signup)

    return signup


def reject_signup(
    db: Session,
    signup_id: int,
    reviewer_id: int,
    review_notes: Optional[str] = None,
    ip_address: Optional[str] = None
) -> Signup:
    signup = db.query(Signup).filter(Signup.id == signup_id).first()
    if not signup:
        raise HTTPException(status_code=404, detail="报名记录不存在")

    if signup.status != SignupStatusEnum.PENDING:
        raise HTTPException(status_code=400, detail="只有待审核的报名可以拒绝")

    signup.status = SignupStatusEnum.REJECTED
    signup.review_time = datetime.utcnow()
    signup.reviewed_by = reviewer_id
    signup.review_notes = review_notes

    db.add(signup)
    db.flush()
    update_shift_current_volunteers(db, signup.shift_id)

    audit_log = AuditLog(
        user_id=reviewer_id,
        action="signup_reject",
        entity_type="signup",
        entity_id=signup_id,
        details=f"审核拒绝报名 {signup_id}",
        ip_address=ip_address
    )
    db.add(audit_log)

    db.commit()
    db.refresh(signup)

    return signup


def cancel_signup(
    db: Session,
    signup_id: int,
    user_id: int,
    is_admin: bool = False,
    ip_address: Optional[str] = None
) -> Signup:
    signup = db.query(Signup).filter(Signup.id == signup_id).first()
    if not signup:
        raise HTTPException(status_code=404, detail="报名记录不存在")

    if not is_admin and signup.volunteer_id != user_id:
        raise HTTPException(status_code=403, detail="只能取消自己的报名")

    if has_checked_in(db, signup.shift_id, signup.volunteer_id):
        raise HTTPException(status_code=400, detail="已签到的班次不能取消报名")

    if signup.status == SignupStatusEnum.CANCELLED:
        return signup

    signup.status = SignupStatusEnum.CANCELLED

    db.add(signup)
    db.flush()
    update_shift_current_volunteers(db, signup.shift_id)

    db.query(Attendance).filter(
        Attendance.shift_id == signup.shift_id,
        Attendance.volunteer_id == signup.volunteer_id,
        Attendance.status == AttendanceStatusEnum.NOT_CHECKED_IN
    ).delete()

    audit_log = AuditLog(
        user_id=user_id,
        action="signup_cancel",
        entity_type="signup",
        entity_id=signup_id,
        details=f"取消报名 {signup_id}",
        ip_address=ip_address
    )
    db.add(audit_log)

    db.commit()
    db.refresh(signup)

    return signup
