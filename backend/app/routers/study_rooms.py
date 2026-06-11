from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import StudyRoom, User, RoleEnum, AuditLog
from ..schemas import StudyRoomCreate, StudyRoomUpdate, StudyRoom as StudyRoomSchema
from ..auth import get_current_user, require_roles

router = APIRouter(prefix="/api/study-rooms", tags=["书房点位"])


@router.get("", response_model=List[StudyRoomSchema])
def list_study_rooms(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(StudyRoom)
    if status:
        query = query.filter(StudyRoom.status == status)
    return query.order_by(StudyRoom.created_at.desc()).all()


@router.get("/{room_id}", response_model=StudyRoomSchema)
def get_study_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room = db.query(StudyRoom).filter(StudyRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="书房点位不存在")
    return room


@router.post("", response_model=StudyRoomSchema)
def create_study_room(
    room_data: StudyRoomCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.OPERATIONS))
):
    room = StudyRoom(**room_data.model_dump())
    db.add(room)
    db.flush()

    audit = AuditLog(
        user_id=current_user.id,
        action="study_room_create",
        entity_type="study_room",
        entity_id=room.id,
        details=f"创建书房点位: {room.name}",
        ip_address=request.client.host if request.client else None
    )
    db.add(audit)

    db.commit()
    db.refresh(room)
    return room


@router.put("/{room_id}", response_model=StudyRoomSchema)
def update_study_room(
    room_id: int,
    room_data: StudyRoomUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.OPERATIONS))
):
    room = db.query(StudyRoom).filter(StudyRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="书房点位不存在")

    update_data = room_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(room, key, value)

    db.add(room)

    audit = AuditLog(
        user_id=current_user.id,
        action="study_room_update",
        entity_type="study_room",
        entity_id=room_id,
        details=f"更新书房点位: {room.name}",
        ip_address=request.client.host if request.client else None
    )
    db.add(audit)

    db.commit()
    db.refresh(room)
    return room


@router.delete("/{room_id}")
def delete_study_room(
    room_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN))
):
    room = db.query(StudyRoom).filter(StudyRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="书房点位不存在")

    room.status = "inactive"
    db.add(room)

    audit = AuditLog(
        user_id=current_user.id,
        action="study_room_delete",
        entity_type="study_room",
        entity_id=room_id,
        details=f"删除书房点位: {room.name}",
        ip_address=request.client.host if request.client else None
    )
    db.add(audit)

    db.commit()
    return {"message": "删除成功"}
