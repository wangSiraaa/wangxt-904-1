import enum
from datetime import datetime, date, time
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Time, Boolean,
    ForeignKey, Text, Enum as SAEnum, Float
)
from sqlalchemy.orm import relationship

from .database import Base


class RoleEnum(str, enum.Enum):
    ADMIN = "admin"
    VOLUNTEER = "volunteer"
    OPERATIONS = "operations"
    TRAINING = "training"


class TrainingStatusEnum(str, enum.Enum):
    NONE = "none"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ShiftTypeEnum(str, enum.Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    NIGHT = "night"


class ShiftStatusEnum(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    FULL = "full"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SignupStatusEnum(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class AttendanceStatusEnum(str, enum.Enum):
    NOT_CHECKED_IN = "not_checked_in"
    PRESENT = "present"
    LATE = "late"
    ABSENT = "absent"


class LeaveStatusEnum(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReplacementTodoStatusEnum(str, enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    COMPLETED = "completed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(50), nullable=False)
    role = Column(SAEnum(RoleEnum), nullable=False, default=RoleEnum.VOLUNTEER)
    phone = Column(String(20))
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    volunteer_profile = relationship("VolunteerProfile", back_populates="user", uselist=False)
    created_shifts = relationship("Shift", back_populates="created_by_user")
    signups = relationship("Signup", back_populates="volunteer", foreign_keys="Signup.volunteer_id")
    attendances = relationship("Attendance", back_populates="volunteer")
    leave_requests = relationship("LeaveRequest", back_populates="volunteer", foreign_keys="LeaveRequest.volunteer_id")
    audit_logs = relationship("AuditLog", back_populates="user")


class StudyRoom(Base):
    __tablename__ = "study_rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    address = Column(String(255))
    description = Column(Text)
    capacity = Column(Integer, default=10)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    shifts = relationship("Shift", back_populates="study_room")


class VolunteerProfile(Base):
    __tablename__ = "volunteer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    real_name = Column(String(50), nullable=False)
    id_card = Column(String(18))
    phone = Column(String(20))
    training_status = Column(SAEnum(TrainingStatusEnum), default=TrainingStatusEnum.NONE)
    training_date = Column(Date)
    training_teacher = Column(String(50))
    skills = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="volunteer_profile")


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    study_room_id = Column(Integer, ForeignKey("study_rooms.id"), nullable=False)
    shift_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    shift_type = Column(SAEnum(ShiftTypeEnum), nullable=False)
    max_volunteers = Column(Integer, nullable=False, default=3)
    current_volunteers = Column(Integer, default=0)
    status = Column(SAEnum(ShiftStatusEnum), default=ShiftStatusEnum.DRAFT)
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    study_room = relationship("StudyRoom", back_populates="shifts")
    created_by_user = relationship("User", back_populates="created_shifts")
    signups = relationship("Signup", back_populates="shift")
    attendances = relationship("Attendance", back_populates="shift")
    leave_requests = relationship("LeaveRequest", back_populates="shift")
    replacement_todos = relationship("ReplacementTodo", back_populates="shift")


class Signup(Base):
    __tablename__ = "signups"

    id = Column(Integer, primary_key=True, index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False, index=True)
    volunteer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(SAEnum(SignupStatusEnum), default=SignupStatusEnum.PENDING)
    signup_time = Column(DateTime, default=datetime.utcnow)
    review_time = Column(DateTime)
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    review_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    shift = relationship("Shift", back_populates="signups")
    volunteer = relationship("User", back_populates="signups", foreign_keys=[volunteer_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False, index=True)
    volunteer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    check_in_time = Column(DateTime)
    check_out_time = Column(DateTime)
    status = Column(SAEnum(AttendanceStatusEnum), default=AttendanceStatusEnum.NOT_CHECKED_IN)
    duration_hours = Column(Float, default=0)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    shift = relationship("Shift", back_populates="attendances")
    volunteer = relationship("User", back_populates="attendances")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False, index=True)
    volunteer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    status = Column(SAEnum(LeaveStatusEnum), default=LeaveStatusEnum.PENDING)
    request_time = Column(DateTime, default=datetime.utcnow)
    review_time = Column(DateTime)
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    review_notes = Column(Text)
    replacement_assigned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    shift = relationship("Shift", back_populates="leave_requests")
    volunteer = relationship("User", back_populates="leave_requests", foreign_keys=[volunteer_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    replacement_todo = relationship("ReplacementTodo", back_populates="leave_request", uselist=False)


class ReplacementTodo(Base):
    __tablename__ = "replacement_todos"

    id = Column(Integer, primary_key=True, index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False, index=True)
    leave_request_id = Column(Integer, ForeignKey("leave_requests.id"), unique=True)
    status = Column(SAEnum(ReplacementTodoStatusEnum), default=ReplacementTodoStatusEnum.PENDING)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    assigned_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    shift = relationship("Shift", back_populates="replacement_todos")
    leave_request = relationship("LeaveRequest", back_populates="replacement_todo")
    assignee = relationship("User", foreign_keys=[assigned_to])


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), index=True)
    entity_id = Column(Integer)
    details = Column(Text)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")


class DuplicateCheckTypeEnum(str, enum.Enum):
    SHIFT_DUPLICATE = "shift_duplicate"
    SIGNUP_DUPLICATE = "signup_duplicate"
    ATTENDANCE_DUPLICATE = "attendance_duplicate"
    TIME_CONFLICT = "time_conflict"
    CROSS_SITE_CONFLICT = "cross_site_conflict"
    TRAINING_REQUIRED = "training_required"


class DuplicateCheckStatusEnum(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


class DuplicateCheck(Base):
    __tablename__ = "duplicate_checks"

    id = Column(Integer, primary_key=True, index=True)
    check_type = Column(SAEnum(DuplicateCheckTypeEnum), nullable=False, index=True)
    status = Column(SAEnum(DuplicateCheckStatusEnum), nullable=False, index=True)
    entity_type = Column(String(50), index=True)
    entity_id = Column(Integer, index=True)
    volunteer_id = Column(Integer, ForeignKey("users.id"), index=True)
    study_room_id = Column(Integer, ForeignKey("study_rooms.id"), index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), index=True)
    conflict_entity_id = Column(Integer)
    conflict_details = Column(Text)
    check_reason = Column(String(255))
    checked_by = Column(Integer, ForeignKey("users.id"))
    check_time = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    volunteer = relationship("User", foreign_keys=[volunteer_id])
    study_room = relationship("StudyRoom")
    shift = relationship("Shift")
    checker = relationship("User", foreign_keys=[checked_by])
