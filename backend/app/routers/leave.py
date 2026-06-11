from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, RoleEnum, LeaveRequest, ReplacementTodo
from ..schemas import (
    LeaveRequestCreate, LeaveRequest as LeaveRequestSchema,
    ReplacementTodo as ReplacementTodoSchema
)
from ..auth import get_current_user, require_roles
from ..services import leave_service as ls

router = APIRouter(prefix="/api/leave", tags=["请假"])


@router.get("", response_model=List[LeaveRequestSchema])
def list_leave_requests(
    shift_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(LeaveRequest)

    if current_user.role == RoleEnum.VOLUNTEER:
        query = query.filter(LeaveRequest.volunteer_id == current_user.id)

    if shift_id:
        query = query.filter(LeaveRequest.shift_id == shift_id)
    if status:
        query = query.filter(LeaveRequest.status == status)

    return query.order_by(LeaveRequest.created_at.desc()).all()


@router.get("/{leave_id}", response_model=LeaveRequestSchema)
def get_leave_request(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="请假记录不存在")

    if current_user.role == RoleEnum.VOLUNTEER and leave.volunteer_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看他人请假记录")

    return leave


@router.post("", response_model=LeaveRequestSchema)
def create_leave(
    leave_data: LeaveRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.VOLUNTEER, RoleEnum.ADMIN))
):
    ip = request.client.host if request.client else None
    return ls.create_leave_request(db, current_user.id, leave_data, ip)


@router.put("/{leave_id}/approve", response_model=LeaveRequestSchema)
def approve_leave(
    leave_id: int,
    request: Request,
    review_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.OPERATIONS))
):
    ip = request.client.host if request.client else None
    return ls.approve_leave(db, leave_id, current_user.id, review_notes, ip)


@router.put("/{leave_id}/reject", response_model=LeaveRequestSchema)
def reject_leave(
    leave_id: int,
    request: Request,
    review_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.OPERATIONS))
):
    ip = request.client.host if request.client else None
    return ls.reject_leave(db, leave_id, current_user.id, review_notes, ip)


@router.get("/replacements/todos", response_model=List[ReplacementTodoSchema])
def list_replacement_todos(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ReplacementTodo)
    if status:
        query = query.filter(ReplacementTodo.status == status)
    return query.order_by(ReplacementTodo.created_at.desc()).all()


@router.put("/replacements/{todo_id}/assign", response_model=ReplacementTodoSchema)
def assign_replacement(
    todo_id: int,
    assigned_to: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.OPERATIONS))
):
    ip = request.client.host if request.client else None
    return ls.assign_replacement(db, todo_id, assigned_to, current_user.id, ip)


@router.put("/replacements/{todo_id}/complete", response_model=ReplacementTodoSchema)
def complete_replacement(
    todo_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.VOLUNTEER, RoleEnum.ADMIN))
):
    ip = request.client.host if request.client else None
    return ls.complete_replacement(db, todo_id, current_user.id, ip)
