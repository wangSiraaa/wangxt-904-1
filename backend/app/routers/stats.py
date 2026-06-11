from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import (
    StudyRoom, Shift, User, Signup, LeaveRequest,
    ReplacementTodo, Attendance, RoleEnum, ShiftStatusEnum,
    SignupStatusEnum, LeaveStatusEnum, ReplacementTodoStatusEnum,
    AttendanceStatusEnum
)
from ..schemas import StatsOverview
from ..auth import get_current_user, require_roles

router = APIRouter(prefix="/api/stats", tags=["运营统计"])


@router.get("/overview", response_model=StatsOverview)
def get_overview_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        RoleEnum.ADMIN, RoleEnum.OPERATIONS
    ))
):
    total_rooms = db.query(func.count(StudyRoom.id)).scalar()
    total_shifts = db.query(func.count(Shift.id)).scalar()
    total_volunteers = db.query(func.count(User.id)).filter(
        User.role == RoleEnum.VOLUNTEER
    ).scalar()
    total_signups = db.query(func.count(Signup.id)).scalar()
    completed_shifts = db.query(func.count(Shift.id)).filter(
        Shift.status == ShiftStatusEnum.COMPLETED
    ).scalar()
    pending_signups = db.query(func.count(Signup.id)).filter(
        Signup.status == SignupStatusEnum.PENDING
    ).scalar()
    pending_leaves = db.query(func.count(LeaveRequest.id)).filter(
        LeaveRequest.status == LeaveStatusEnum.PENDING
    ).scalar()
    replacement_todos = db.query(func.count(ReplacementTodo.id)).filter(
        ReplacementTodo.status == ReplacementTodoStatusEnum.PENDING
    ).scalar()

    return StatsOverview(
        total_rooms=total_rooms,
        total_shifts=total_shifts,
        total_volunteers=total_volunteers,
        total_signups=total_signups,
        completed_shifts=completed_shifts,
        pending_signups=pending_signups,
        pending_leaves=pending_leaves,
        replacement_todos=replacement_todos
    )


@router.get("/volunteer-hours")
def get_volunteer_hours(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        RoleEnum.ADMIN, RoleEnum.OPERATIONS
    ))
):
    results = db.query(
        User.id,
        User.name,
        func.sum(Attendance.duration_hours).label("total_hours"),
        func.count(Attendance.id).label("shift_count")
    ).join(
        Attendance, Attendance.volunteer_id == User.id
    ).filter(
        User.role == RoleEnum.VOLUNTEER,
        Attendance.status.in_([AttendanceStatusEnum.PRESENT, AttendanceStatusEnum.LATE])
    ).group_by(User.id).all()

    return [
        {
            "volunteer_id": r.id,
            "name": r.name,
            "total_hours": r.total_hours or 0,
            "shift_count": r.shift_count or 0
        }
        for r in results
    ]


@router.get("/room-usage")
def get_room_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(
        RoleEnum.ADMIN, RoleEnum.OPERATIONS
    ))
):
    results = db.query(
        StudyRoom.id,
        StudyRoom.name,
        func.count(Shift.id).label("total_shifts"),
    ).outerjoin(
        Shift, Shift.study_room_id == StudyRoom.id
    ).group_by(StudyRoom.id).all()

    return [
        {
            "room_id": r.id,
            "name": r.name,
            "total_shifts": r.total_shifts or 0
        }
        for r in results
    ]
