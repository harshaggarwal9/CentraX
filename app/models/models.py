from enum import Enum
from datetime import datetime
from sqlalchemy.sql import func
from app.db.base import Base

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Text,
    Enum as SAEnum,
    UniqueConstraint,
)


class RoleEnum(str, Enum):
    admin = "admin"
    coordinator = "coordinator"
    teacher = "teacher"
    student = "student"


class ContentTypeEnum(str, Enum):
    video = "video"
    pdf = "pdf"
    image = "image"
    other = "other"


class PaymentStatusEnum(str, Enum):
    pending = "pending"
    success = "success"
    failed = "failed"
    refunded = "refunded"


class AuthProviderEnum(str, Enum):
    password = "password"    
    google = "google"          


class users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    firebase_uid = Column(String, unique=True, index=True, nullable=False)
    auth_provider = Column(SAEnum(AuthProviderEnum), nullable=True)

    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(SAEnum(RoleEnum), default=RoleEnum.student, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
    )


class UserAuthProviders(Base):
    __tablename__ = "user_auth_providers"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(SAEnum(AuthProviderEnum), nullable=False)
    provider_uid = Column(String, nullable=False)  # Firebase provider-specific uid


class batches(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)

    coordinator_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class enrollments(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    role_in_batch = Column(String, default="student")


class contents(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    content_type = Column(
        SAEnum(ContentTypeEnum),
        default=ContentTypeEnum.video,
        index=True,
    )

    storage_url = Column(String, nullable=False)

    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_public = Column(Boolean, default=False)


class comments(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_public = Column(Boolean, default=True)


class notifications(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    channel = Column(String, default="in-app")
    is_read = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class schedules(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    location = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

class payments(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(8), default="INR")
    status = Column(SAEnum(PaymentStatusEnum), default=PaymentStatusEnum.pending, index=True)
    reference = Column(String, nullable=True)
    payment_metadata = Column(Text, nullable=True)  # renamed

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class teachers(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    subjects = Column(Text, nullable=True)    
    experience = Column(Integer, nullable=True)
    qualifications = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

