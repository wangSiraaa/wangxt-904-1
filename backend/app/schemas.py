from datetime import datetime, date, time
from typing import Optional, List
import enum
from pydantic import BaseModel, Field

from .models import (
    RoleEnum, TrainingStatusEnum, ShiftTypeEnum, ShiftStatusEnum,
    SignupStatusEnum, AttendanceStatusEnum, LeaveStatusEnum,
    ReplacementTodoStatusEnum
)


class UserBase(BaseModel):
    username: str
    name: str
    role: RoleEnum
    phone: Optional[str] = None
    email: Optional[str] = None


class UserCreate(UserBase):
    password: str


class User(BaseModel):
    id: int
    username: str
    name: str
    role: RoleEnum
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class StudyRoomBase(BaseModel):
    name: str
    address: Optional[str] = None
    description: Optional[str] = None
    capacity: int = 10
    status: str = "active"


class StudyRoomCreate(StudyRoomBase):
    pass


class StudyRoomUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[str] = None


class StudyRoom(StudyRoomBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VolunteerProfileBase(BaseModel):
    real_name: str
    id_card: Optional[str] = None
    phone: Optional[str] = None
    training_status: TrainingStatusEnum = TrainingStatusEnum.NONE
    training_date: Optional[date] = None
    training_teacher: Optional[str] = None
    skills: Optional[str] = None


class VolunteerProfileCreate(VolunteerProfileBase):
    user_id: int


class VolunteerProfileUpdate(BaseModel):
    real_name: Optional[str] = None
    id_card: Optional[str] = None
    phone: Optional[str] = None
    training_status: Optional[TrainingStatusEnum] = None
    training_date: Optional[date] = None
    training_teacher: Optional[str] = None
    skills: Optional[str] = None


class VolunteerProfile(VolunteerProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VolunteerDetail(BaseModel):
    id: int
    username: str
    name: str
    role: RoleEnum
    phone: Optional[str] = None
    volunteer_profile: Optional[VolunteerProfile] = None

    class Config:
        from_attributes = True


class ShiftBase(BaseModel):
    study_room_id: int
    shift_date: date
    start_time: time
    end_time: time
    shift_type: ShiftTypeEnum
    max_volunteers: int = 3
    notes: Optional[str] = None


class ShiftCreate(ShiftBase):
    pass


class ShiftUpdate(BaseModel):
    study_room_id: Optional[int] = None
    shift_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    shift_type: Optional[ShiftTypeEnum] = None
    max_volunteers: Optional[int] = None
    notes: Optional[str] = None
    status: Optional[ShiftStatusEnum] = None


class Shift(ShiftBase):
    id: int
    status: ShiftStatusEnum
    current_volunteers: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    study_room: Optional[StudyRoom] = None

    class Config:
        from_attributes = True


class ShiftWithDetails(Shift):
    signups: Optional[List] = None


class SignupBase(BaseModel):
    shift_id: int


class SignupCreate(SignupBase):
    pass


class SignupUpdate(BaseModel):
    status: Optional[SignupStatusEnum] = None
    review_notes: Optional[str] = None


class Signup(BaseModel):
    id: int
    shift_id: int
    volunteer_id: int
    status: SignupStatusEnum
    signup_time: datetime
    review_time: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SignupWithDetails(Signup):
    shift: Optional[Shift] = None
    volunteer: Optional[User] = None


class AttendanceBase(BaseModel):
    shift_id: int


class Attendance(BaseModel):
    id: int
    shift_id: int
    volunteer_id: int
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    status: AttendanceStatusEnum
    duration_hours: float = 0
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AttendanceWithDetails(Attendance):
    shift: Optional[Shift] = None
    volunteer: Optional[User] = None


class LeaveRequestBase(BaseModel):
    shift_id: int
    reason: str


class LeaveRequestCreate(LeaveRequestBase):
    pass


class LeaveRequestUpdate(BaseModel):
    status: Optional[LeaveStatusEnum] = None
    review_notes: Optional[str] = None


class LeaveRequest(BaseModel):
    id: int
    shift_id: int
    volunteer_id: int
    reason: str
    status: LeaveStatusEnum
    request_time: datetime
    review_time: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    review_notes: Optional[str] = None
    replacement_assigned: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReplacementTodoBase(BaseModel):
    shift_id: int
    leave_request_id: int


class ReplacementTodo(BaseModel):
    id: int
    shift_id: int
    leave_request_id: int
    status: ReplacementTodoStatusEnum
    assigned_to: Optional[int] = None
    assigned_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogBase(BaseModel):
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    details: Optional[str] = None


class AuditLog(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class StatsOverview(BaseModel):
    total_rooms: int
    total_shifts: int
    total_volunteers: int
    total_signups: int
    completed_shifts: int
    pending_signups: int
    pending_leaves: int
    replacement_todos: int


class ConflictInfo(BaseModel):
    has_conflict: bool
    conflict_type: Optional[str] = None
    conflict_details: Optional[str] = None
    conflicting_shift: Optional[Shift] = None


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


class DuplicateCheckTypeEnum(str, enum.Enum):
    SHIFT_DUPLICATE = "shift_duplicate"
    SIGNUP_DUPLICATE = "signup_duplicate"
    ATTENDANCE_DUPLICATE = "attendance_duplicate"
    TIME_CONFLICT = "time_conflict"
    CROSS_SITE_CONFLICT = "cross_site_conflict"
    TRAINING_REQUIRED = "training_required"
    STUDY_ROOM_NAME_DUPLICATE = "study_room_name_duplicate"
    STUDY_ROOM_ADDRESS_DUPLICATE = "study_room_address_duplicate"


class DuplicateCheckStatusEnum(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


class DuplicateCheckBase(BaseModel):
    check_type: DuplicateCheckTypeEnum
    status: DuplicateCheckStatusEnum
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    volunteer_id: Optional[int] = None
    study_room_id: Optional[int] = None
    shift_id: Optional[int] = None
    conflict_entity_id: Optional[int] = None
    conflict_details: Optional[str] = None
    check_reason: Optional[str] = None


class DuplicateCheckCreate(DuplicateCheckBase):
    pass


class DuplicateCheck(DuplicateCheckBase):
    id: int
    checked_by: Optional[int] = None
    check_time: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class DuplicateCheckWithDetails(DuplicateCheck):
    volunteer: Optional[User] = None
    study_room: Optional[StudyRoom] = None
    shift: Optional[Shift] = None
    checker: Optional[User] = None


class DuplicateCheckResult(BaseModel):
    has_duplicate: bool
    check_type: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    conflict_details: Optional[str] = None
    conflicting_entity_id: Optional[int] = None
    check_id: Optional[int] = None
