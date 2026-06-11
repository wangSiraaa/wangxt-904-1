from datetime import datetime, date
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from ..models import (
    DuplicateCheck, DuplicateCheckTypeEnum, DuplicateCheckStatusEnum,
    Shift, Signup, Attendance, StudyRoom, User,
    ShiftStatusEnum, SignupStatusEnum, AttendanceStatusEnum,
    ShiftTypeEnum, TrainingStatusEnum, VolunteerProfile
)
from ..schemas import DuplicateCheckCreate, DuplicateCheckResult


def create_duplicate_check_record(
    db: Session,
    check_type: DuplicateCheckTypeEnum,
    status: DuplicateCheckStatusEnum,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    volunteer_id: Optional[int] = None,
    study_room_id: Optional[int] = None,
    shift_id: Optional[int] = None,
    conflict_entity_id: Optional[int] = None,
    conflict_details: Optional[str] = None,
    check_reason: Optional[str] = None,
    checked_by: Optional[int] = None
) -> DuplicateCheck:
    check_record = DuplicateCheck(
        check_type=check_type,
        status=status,
        entity_type=entity_type,
        entity_id=entity_id,
        volunteer_id=volunteer_id,
        study_room_id=study_room_id,
        shift_id=shift_id,
        conflict_entity_id=conflict_entity_id,
        conflict_details=conflict_details,
        check_reason=check_reason,
        checked_by=checked_by,
        check_time=datetime.utcnow()
    )
    db.add(check_record)
    db.flush()
    return check_record


def check_shift_duplicate(
    db: Session,
    study_room_id: int,
    shift_date: date,
    start_time: datetime.time,
    end_time: datetime.time,
    exclude_shift_id: Optional[int] = None,
    checked_by: Optional[int] = None
) -> Tuple[bool, Optional[DuplicateCheck], Optional[Shift]]:
    query = db.query(Shift).filter(
        Shift.study_room_id == study_room_id,
        Shift.shift_date == shift_date,
        Shift.status != ShiftStatusEnum.CANCELLED
    )

    if exclude_shift_id:
        query = query.filter(Shift.id != exclude_shift_id)

    existing_shifts = query.all()

    target_start = datetime.combine(shift_date, start_time)
    target_end = datetime.combine(shift_date, end_time)

    for shift in existing_shifts:
        other_start = datetime.combine(shift.shift_date, shift.start_time)
        other_end = datetime.combine(shift.shift_date, shift.end_time)

        if target_start < other_end and target_end > other_start:
            check_record = create_duplicate_check_record(
                db,
                check_type=DuplicateCheckTypeEnum.SHIFT_DUPLICATE,
                status=DuplicateCheckStatusEnum.FAIL,
                entity_type="shift",
                study_room_id=study_room_id,
                shift_id=exclude_shift_id,
                conflict_entity_id=shift.id,
                conflict_details=f"与班次 {shift.id} 时间重叠: {shift.start_time} - {shift.end_time}",
                check_reason="同时段存在重复班次",
                checked_by=checked_by
            )
            return True, check_record, shift

    check_record = create_duplicate_check_record(
        db,
        check_type=DuplicateCheckTypeEnum.SHIFT_DUPLICATE,
        status=DuplicateCheckStatusEnum.PASS,
        entity_type="shift",
        study_room_id=study_room_id,
        shift_id=exclude_shift_id,
        check_reason="无重复班次",
        checked_by=checked_by
    )
    return False, check_record, None


def check_signup_duplicate(
    db: Session,
    volunteer_id: int,
    shift_id: int,
    checked_by: Optional[int] = None
) -> Tuple[bool, Optional[DuplicateCheck], Optional[Signup]]:
    existing_signup = db.query(Signup).filter(
        Signup.volunteer_id == volunteer_id,
        Signup.shift_id == shift_id,
        Signup.status.in_([SignupStatusEnum.PENDING, SignupStatusEnum.APPROVED])
    ).first()

    if existing_signup:
        check_record = create_duplicate_check_record(
            db,
            check_type=DuplicateCheckTypeEnum.SIGNUP_DUPLICATE,
            status=DuplicateCheckStatusEnum.FAIL,
            entity_type="signup",
            volunteer_id=volunteer_id,
            shift_id=shift_id,
            conflict_entity_id=existing_signup.id,
            conflict_details=f"已存在报名记录: {existing_signup.id} 状态: {existing_signup.status}",
            check_reason="同一班次重复报名",
            checked_by=checked_by
        )
        return True, check_record, existing_signup

    check_record = create_duplicate_check_record(
        db,
        check_type=DuplicateCheckTypeEnum.SIGNUP_DUPLICATE,
        status=DuplicateCheckStatusEnum.PASS,
        entity_type="signup",
        volunteer_id=volunteer_id,
        shift_id=shift_id,
        check_reason="无重复报名",
        checked_by=checked_by
    )
    return False, check_record, None


def check_attendance_duplicate(
    db: Session,
    volunteer_id: int,
    shift_id: int,
    checked_by: Optional[int] = None
) -> Tuple[bool, Optional[DuplicateCheck], Optional[Attendance]]:
    existing_attendance = db.query(Attendance).filter(
        Attendance.volunteer_id == volunteer_id,
        Attendance.shift_id == shift_id,
        Attendance.status.in_([AttendanceStatusEnum.PRESENT, AttendanceStatusEnum.LATE])
    ).first()

    if existing_attendance:
        check_record = create_duplicate_check_record(
            db,
            check_type=DuplicateCheckTypeEnum.ATTENDANCE_DUPLICATE,
            status=DuplicateCheckStatusEnum.FAIL,
            entity_type="attendance",
            volunteer_id=volunteer_id,
            shift_id=shift_id,
            conflict_entity_id=existing_attendance.id,
            conflict_details=f"已存在签到记录: {existing_attendance.id} 状态: {existing_attendance.status}",
            check_reason="同一班次重复签到",
            checked_by=checked_by
        )
        return True, check_record, existing_attendance

    check_record = create_duplicate_check_record(
        db,
        check_type=DuplicateCheckTypeEnum.ATTENDANCE_DUPLICATE,
        status=DuplicateCheckStatusEnum.PASS,
        entity_type="attendance",
        volunteer_id=volunteer_id,
        shift_id=shift_id,
        check_reason="无重复签到",
        checked_by=checked_by
    )
    return False, check_record, None


def check_time_conflict(
    db: Session,
    volunteer_id: int,
    shift_id: int,
    exclude_signup_id: Optional[int] = None,
    checked_by: Optional[int] = None
) -> Tuple[bool, Optional[DuplicateCheck], Optional[Shift]]:
    target_shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not target_shift:
        check_record = create_duplicate_check_record(
            db,
            check_type=DuplicateCheckTypeEnum.TIME_CONFLICT,
            status=DuplicateCheckStatusEnum.FAIL,
            entity_type="shift",
            volunteer_id=volunteer_id,
            shift_id=shift_id,
            conflict_details="班次不存在",
            check_reason="目标班次不存在",
            checked_by=checked_by
        )
        return True, check_record, None

    approved_signups = db.query(Signup).filter(
        Signup.volunteer_id == volunteer_id,
        Signup.status == SignupStatusEnum.APPROVED,
        Signup.shift_id != shift_id
    ).all()

    if exclude_signup_id:
        approved_signups = [
            s for s in approved_signups if s.id != exclude_signup_id
        ]

    target_start = datetime.combine(target_shift.shift_date, target_shift.start_time)
    target_end = datetime.combine(target_shift.shift_date, target_shift.end_time)

    for signup in approved_signups:
        other_shift = signup.shift
        if not other_shift:
            continue

        if other_shift.study_room_id != target_shift.study_room_id:
            if other_shift.shift_date == target_shift.shift_date:
                check_record = create_duplicate_check_record(
                    db,
                    check_type=DuplicateCheckTypeEnum.CROSS_SITE_CONFLICT,
                    status=DuplicateCheckStatusEnum.WARNING,
                    entity_type="signup",
                    volunteer_id=volunteer_id,
                    shift_id=shift_id,
                    study_room_id=target_shift.study_room_id,
                    conflict_entity_id=other_shift.id,
                    conflict_details=f"同日跨点位冲突: {other_shift.study_room.name} {other_shift.start_time} - {other_shift.end_time}",
                    check_reason="同日在不同点位排班",
                    checked_by=checked_by
                )
                return True, check_record, other_shift

        other_start = datetime.combine(other_shift.shift_date, other_shift.start_time)
        other_end = datetime.combine(other_shift.shift_date, other_shift.end_time)

        if target_start < other_end and target_end > other_start:
            check_record = create_duplicate_check_record(
                db,
                check_type=DuplicateCheckTypeEnum.TIME_CONFLICT,
                status=DuplicateCheckStatusEnum.FAIL,
                entity_type="signup",
                volunteer_id=volunteer_id,
                shift_id=shift_id,
                study_room_id=target_shift.study_room_id,
                conflict_entity_id=other_shift.id,
                conflict_details=f"时间重叠冲突: {other_shift.study_room.name} {other_shift.start_time} - {other_shift.end_time}",
                check_reason="同时段已排班",
                checked_by=checked_by
            )
            return True, check_record, other_shift

    check_record = create_duplicate_check_record(
        db,
        check_type=DuplicateCheckTypeEnum.TIME_CONFLICT,
        status=DuplicateCheckStatusEnum.PASS,
        entity_type="signup",
        volunteer_id=volunteer_id,
        shift_id=shift_id,
        check_reason="无时间冲突",
        checked_by=checked_by
    )
    return False, check_record, None


def check_training_requirement(
    db: Session,
    volunteer_id: int,
    shift_id: int,
    checked_by: Optional[int] = None
) -> Tuple[bool, Optional[DuplicateCheck]]:
    target_shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not target_shift:
        check_record = create_duplicate_check_record(
            db,
            check_type=DuplicateCheckTypeEnum.TRAINING_REQUIRED,
            status=DuplicateCheckStatusEnum.FAIL,
            entity_type="shift",
            volunteer_id=volunteer_id,
            shift_id=shift_id,
            conflict_details="班次不存在",
            check_reason="目标班次不存在",
            checked_by=checked_by
        )
        return True, check_record

    if target_shift.shift_type != ShiftTypeEnum.NIGHT:
        check_record = create_duplicate_check_record(
            db,
            check_type=DuplicateCheckTypeEnum.TRAINING_REQUIRED,
            status=DuplicateCheckStatusEnum.PASS,
            entity_type="signup",
            volunteer_id=volunteer_id,
            shift_id=shift_id,
            check_reason="非晚班，无需培训",
            checked_by=checked_by
        )
        return False, check_record

    volunteer_profile = db.query(VolunteerProfile).filter(
        VolunteerProfile.user_id == volunteer_id
    ).first()

    if not volunteer_profile or volunteer_profile.training_status != TrainingStatusEnum.COMPLETED:
        check_record = create_duplicate_check_record(
            db,
            check_type=DuplicateCheckTypeEnum.TRAINING_REQUIRED,
            status=DuplicateCheckStatusEnum.FAIL,
            entity_type="signup",
            volunteer_id=volunteer_id,
            shift_id=shift_id,
            conflict_details=f"晚班需要培训，当前状态: {volunteer_profile.training_status if volunteer_profile else '无档案'}",
            check_reason="未完成培训不能排晚班",
            checked_by=checked_by
        )
        return True, check_record

    check_record = create_duplicate_check_record(
        db,
        check_type=DuplicateCheckTypeEnum.TRAINING_REQUIRED,
        status=DuplicateCheckStatusEnum.PASS,
        entity_type="signup",
        volunteer_id=volunteer_id,
        shift_id=shift_id,
        check_reason="已完成培训",
        checked_by=checked_by
    )
    return False, check_record


def perform_full_signup_check(
    db: Session,
    volunteer_id: int,
    shift_id: int,
    checked_by: Optional[int] = None,
    exclude_signup_id: Optional[int] = None
) -> List[DuplicateCheck]:
    results = []

    has_dup, dup_check, _ = check_signup_duplicate(
        db, volunteer_id, shift_id, checked_by
    )
    results.append(dup_check)

    has_conflict, conflict_check, _ = check_time_conflict(
        db, volunteer_id, shift_id, exclude_signup_id, checked_by
    )
    results.append(conflict_check)

    has_training, training_check = check_training_requirement(
        db, volunteer_id, shift_id, checked_by
    )
    results.append(training_check)

    db.commit()
    return results


def get_duplicate_checks(
    db: Session,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    volunteer_id: Optional[int] = None,
    shift_id: Optional[int] = None,
    check_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[DuplicateCheck]:
    query = db.query(DuplicateCheck)

    if entity_type:
        query = query.filter(DuplicateCheck.entity_type == entity_type)
    if entity_id:
        query = query.filter(DuplicateCheck.entity_id == entity_id)
    if volunteer_id:
        query = query.filter(DuplicateCheck.volunteer_id == volunteer_id)
    if shift_id:
        query = query.filter(DuplicateCheck.shift_id == shift_id)
    if check_type:
        query = query.filter(DuplicateCheck.check_type == check_type)
    if status:
        query = query.filter(DuplicateCheck.status == status)

    return query.order_by(DuplicateCheck.check_time.desc()).offset(offset).limit(limit).all()


def get_duplicate_check_timeline(
    db: Session,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    volunteer_id: Optional[int] = None,
    shift_id: Optional[int] = None,
    days: int = 30
) -> List[dict]:
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)

    query = db.query(DuplicateCheck).filter(DuplicateCheck.check_time >= cutoff)

    if entity_type:
        query = query.filter(DuplicateCheck.entity_type == entity_type)
    if entity_id:
        query = query.filter(DuplicateCheck.entity_id == entity_id)
    if volunteer_id:
        query = query.filter(DuplicateCheck.volunteer_id == volunteer_id)
    if shift_id:
        query = query.filter(DuplicateCheck.shift_id == shift_id)

    checks = query.order_by(DuplicateCheck.check_time.desc()).all()

    timeline = []
    for check in checks:
        timeline.append({
            "id": check.id,
            "check_type": check.check_type.value,
            "status": check.status.value,
            "entity_type": check.entity_type,
            "entity_id": check.entity_id,
            "volunteer_id": check.volunteer_id,
            "study_room_id": check.study_room_id,
            "shift_id": check.shift_id,
            "conflict_entity_id": check.conflict_entity_id,
            "conflict_details": check.conflict_details,
            "check_reason": check.check_reason,
            "check_time": check.check_time,
            "study_room_name": check.study_room.name if check.study_room else None,
            "volunteer_name": check.volunteer.name if check.volunteer else None,
            "checker_name": check.checker.name if check.checker else None,
        })

    return timeline
