from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..models import (
    LeaveRequest, Shift, Signup, Attendance, ReplacementTodo, AuditLog,
    LeaveStatusEnum, SignupStatusEnum, AttendanceStatusEnum,
    ReplacementTodoStatusEnum
)
from ..schemas import LeaveRequestCreate
from .shift_service import update_shift_current_volunteers


def create_leave_request(
    db: Session,
    volunteer_id: int,
    leave_data: LeaveRequestCreate,
    ip_address: Optional[str] = None
) -> LeaveRequest:
    shift = db.query(Shift).filter(Shift.id == leave_data.shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="班次不存在")

    signup = db.query(Signup).filter(
        Signup.shift_id == leave_data.shift_id,
        Signup.volunteer_id == volunteer_id,
        Signup.status == SignupStatusEnum.APPROVED
    ).first()

    if not signup:
        raise HTTPException(status_code=400, detail="您没有该班次的有效报名记录")

    attendance = db.query(Attendance).filter(
        Attendance.shift_id == leave_data.shift_id,
        Attendance.volunteer_id == volunteer_id,
        Attendance.status.in_([AttendanceStatusEnum.PRESENT, AttendanceStatusEnum.LATE])
    ).first()

    if attendance:
        raise HTTPException(status_code=400, detail="已签到的班次不能请假")

    existing_leave = db.query(LeaveRequest).filter(
        LeaveRequest.shift_id == leave_data.shift_id,
        LeaveRequest.volunteer_id == volunteer_id,
        LeaveRequest.status.in_([LeaveStatusEnum.PENDING, LeaveStatusEnum.APPROVED])
    ).first()

    if existing_leave:
        return existing_leave

    leave = LeaveRequest(
        shift_id=leave_data.shift_id,
        volunteer_id=volunteer_id,
        reason=leave_data.reason,
        status=LeaveStatusEnum.PENDING,
        request_time=datetime.utcnow()
    )

    db.add(leave)

    audit_log = AuditLog(
        user_id=volunteer_id,
        action="leave_create",
        entity_type="leave",
        entity_id=leave.id,
        details=f"提交请假申请，班次: {leave_data.shift_id}",
        ip_address=ip_address
    )
    db.add(audit_log)

    db.commit()
    db.refresh(leave)

    return leave


def approve_leave(
    db: Session,
    leave_id: int,
    reviewer_id: int,
    review_notes: Optional[str] = None,
    ip_address: Optional[str] = None
) -> LeaveRequest:
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="请假记录不存在")

    if leave.status != LeaveStatusEnum.PENDING:
        raise HTTPException(status_code=400, detail="只有待审核的请假可以审批")

    leave.status = LeaveStatusEnum.APPROVED
    leave.review_time = datetime.utcnow()
    leave.reviewed_by = reviewer_id
    leave.review_notes = review_notes

    db.add(leave)

    signup = db.query(Signup).filter(
        Signup.shift_id == leave.shift_id,
        Signup.volunteer_id == leave.volunteer_id,
        Signup.status == SignupStatusEnum.APPROVED
    ).first()

    if signup:
        signup.status = SignupStatusEnum.CANCELLED
        db.add(signup)
        db.flush()
        update_shift_current_volunteers(db, leave.shift_id)

    db.query(Attendance).filter(
        Attendance.shift_id == leave.shift_id,
        Attendance.volunteer_id == leave.volunteer_id,
        Attendance.status == AttendanceStatusEnum.NOT_CHECKED_IN
    ).delete()

    todo = ReplacementTodo(
        shift_id=leave.shift_id,
        leave_request_id=leave.id,
        status=ReplacementTodoStatusEnum.PENDING
    )
    db.add(todo)
    leave.replacement_assigned = False

    audit_log = AuditLog(
        user_id=reviewer_id,
        action="leave_approve",
        entity_type="leave",
        entity_id=leave_id,
        details=f"审核通过请假 {leave_id}，生成补位待办",
        ip_address=ip_address
    )
    db.add(audit_log)

    db.commit()
    db.refresh(leave)

    return leave


def reject_leave(
    db: Session,
    leave_id: int,
    reviewer_id: int,
    review_notes: Optional[str] = None,
    ip_address: Optional[str] = None
) -> LeaveRequest:
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="请假记录不存在")

    if leave.status != LeaveStatusEnum.PENDING:
        raise HTTPException(status_code=400, detail="只有待审核的请假可以拒绝")

    leave.status = LeaveStatusEnum.REJECTED
    leave.review_time = datetime.utcnow()
    leave.reviewed_by = reviewer_id
    leave.review_notes = review_notes

    db.add(leave)

    audit_log = AuditLog(
        user_id=reviewer_id,
        action="leave_reject",
        entity_type="leave",
        entity_id=leave_id,
        details=f"审核拒绝请假 {leave_id}",
        ip_address=ip_address
    )
    db.add(audit_log)

    db.commit()
    db.refresh(leave)

    return leave


def assign_replacement(
    db: Session,
    todo_id: int,
    assigned_to: int,
    assigner_id: int,
    ip_address: Optional[str] = None
) -> ReplacementTodo:
    todo = db.query(ReplacementTodo).filter(ReplacementTodo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="补位待办不存在")

    todo.status = ReplacementTodoStatusEnum.ASSIGNED
    todo.assigned_to = assigned_to
    todo.assigned_at = datetime.utcnow()

    db.add(todo)

    leave = db.query(LeaveRequest).filter(LeaveRequest.id == todo.leave_request_id).first()
    if leave:
        leave.replacement_assigned = True
        db.add(leave)

    audit_log = AuditLog(
        user_id=assigner_id,
        action="replacement_assign",
        entity_type="replacement",
        entity_id=todo_id,
        details=f"分配补位给志愿者 {assigned_to}",
        ip_address=ip_address
    )
    db.add(audit_log)

    db.commit()
    db.refresh(todo)

    return todo


def complete_replacement(
    db: Session,
    todo_id: int,
    user_id: int,
    ip_address: Optional[str] = None
) -> ReplacementTodo:
    todo = db.query(ReplacementTodo).filter(ReplacementTodo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="补位待办不存在")

    if todo.assigned_to != user_id:
        raise HTTPException(status_code=403, detail="只能处理分配给自己的补位")

    todo.status = ReplacementTodoStatusEnum.COMPLETED

    db.add(todo)

    signup = Signup(
        shift_id=todo.shift_id,
        volunteer_id=user_id,
        status=SignupStatusEnum.APPROVED,
        signup_time=datetime.utcnow(),
        review_time=datetime.utcnow(),
        reviewed_by=user_id
    )
    db.add(signup)
    db.flush()
    update_shift_current_volunteers(db, todo.shift_id)

    attendance = Attendance(
        shift_id=todo.shift_id,
        volunteer_id=user_id,
        status=AttendanceStatusEnum.NOT_CHECKED_IN
    )
    db.add(attendance)

    audit_log = AuditLog(
        user_id=user_id,
        action="replacement_complete",
        entity_type="replacement",
        entity_id=todo_id,
        details=f"完成补位 {todo_id}",
        ip_address=ip_address
    )
    db.add(audit_log)

    db.commit()
    db.refresh(todo)

    return todo
