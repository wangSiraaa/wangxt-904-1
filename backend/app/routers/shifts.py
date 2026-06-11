from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Shift, StudyRoom, User, RoleEnum, AuditLog, ShiftStatusEnum
from ..schemas import ShiftCreate, ShiftUpdate, Shift as ShiftSchema
from ..auth import get_current_user, require_roles

router = APIRouter(prefix="/api/shifts", tags=["班次"])


@router.get("", response_model=List[ShiftSchema])
def list_shifts(
    study_room_id: Optional[int] = None,
    shift_date: Optional[date] = None,
    status: Optional[ShiftStatusEnum] = None,
    shift_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Shift)
    if study_room_id:
        query = query.filter(Shift.study_room_id == study_room_id)
    if shift_date:
        query = query.filter(Shift.shift_date == shift_date)
    if status:
        query = query.filter(Shift.status == status)
    if shift_type:
        query = query.filter(Shift.shift_type == shift_type)
    return query.order_by(Shift.shift_date.desc(), Shift.start_time.asc()).all()


@router.get("/{shift_id}", response_model=ShiftSchema)
def get_shift(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="班次不存在")
    return shift


@router.post("", response_model=ShiftSchema)
def create_shift(
    shift_data: ShiftCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.OPERATIONS))
):
    room = db.query(StudyRoom).filter(StudyRoom.id == shift_data.study_room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="书房点位不存在")

    shift = Shift(
        **shift_data.model_dump(),
        status=ShiftStatusEnum.DRAFT,
        created_by=current_user.id
    )
    db.add(shift)
    db.flush()

    audit = AuditLog(
        user_id=current_user.id,
        action="shift_create",
        entity_type="shift",
        entity_id=shift.id,
        details=f"创建班次: {shift.id}",
        ip_address=request.client.host if request.client else None
    )
    db.add(audit)

    db.commit()
    db.refresh(shift)
    return shift


@router.put("/{shift_id}", response_model=ShiftSchema)
def update_shift(
    shift_id: int,
    shift_data: ShiftUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.OPERATIONS))
):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="班次不存在")

    update_data = shift_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(shift, key, value)

    db.add(shift)

    audit = AuditLog(
        user_id=current_user.id,
        action="shift_update",
        entity_type="shift",
        entity_id=shift_id,
        details=f"更新班次: {shift_id}",
        ip_address=request.client.host if request.client else None
    )
    db.add(audit)

    db.commit()
    db.refresh(shift)
    return shift


@router.post("/{shift_id}/publish", response_model=ShiftSchema)
def publish_shift(
    shift_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.OPERATIONS))
):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="班次不存在")

    if shift.status not in [ShiftStatusEnum.DRAFT, ShiftStatusEnum.CANCELLED]:
        if shift.status == ShiftStatusEnum.PUBLISHED or shift.status == ShiftStatusEnum.FULL:
            return shift

    shift.status = ShiftStatusEnum.PUBLISHED
    db.add(shift)

    audit = AuditLog(
        user_id=current_user.id,
        action="shift_publish",
        entity_type="shift",
        entity_id=shift_id,
        details=f"发布班次: {shift_id}",
        ip_address=request.client.host if request.client else None
    )
    db.add(audit)

    db.commit()
    db.refresh(shift)
    return shift


@router.post("/{shift_id}/cancel", response_model=ShiftSchema)
def cancel_shift(
    shift_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN))
):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="班次不存在")

    if shift.status == ShiftStatusEnum.CANCELLED:
        return shift

    shift.status = ShiftStatusEnum.CANCELLED
    db.add(shift)

    audit = AuditLog(
        user_id=current_user.id,
        action="shift_cancel",
        entity_type="shift",
        entity_id=shift_id,
        details=f"取消班次: {shift_id}",
        ip_address=request.client.host if request.client else None
    )
    db.add(audit)

    db.commit()
    db.refresh(shift)
    return shift


@router.delete("/{shift_id}")
def delete_shift(
    shift_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN))
):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="班次不存在")

    if shift.signups and len(shift.signups) > 0:
        raise HTTPException(status_code=400, detail="已有报名的班次不能删除，请先取消班次")

    db.delete(shift)

    audit = AuditLog(
        user_id=current_user.id,
        action="shift_delete",
        entity_type="shift",
        entity_id=shift_id,
        details=f"删除班次: {shift_id}",
        ip_address=request.client.host if request.client else None
    )
    db.add(audit)

    db.commit()
    return {"message": "删除成功"}
