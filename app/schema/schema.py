from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, constr
from ..models.models import RoleEnum, ContentTypeEnum, PaymentStatusEnum


class User(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    role: RoleEnum = RoleEnum.student
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)



class Batch(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    coordinator_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Enrollment(BaseModel):
    id: int
    batch_id: int
    student_id: int
    joined_at: datetime
    is_active: bool = True
    role_in_batch: str = "student"

    model_config = ConfigDict(from_attributes=True)


class Content(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    content_type: ContentTypeEnum = ContentTypeEnum.video
    storage_url: str
    uploader_id: int
    batch_id: Optional[int] = None
    created_at: datetime
    is_public: bool = False

    model_config = ConfigDict(from_attributes=True)

class Comment(BaseModel):
    id: int
    content_id: int
    author_id: int
    text: str
    created_at: datetime
    is_public: bool = True

    model_config = ConfigDict(from_attributes=True)


class Schedule(BaseModel):
    id: int
    batch_id: int
    created_by: Optional[int] = None
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Payment(BaseModel):
    id: int
    payer_id: int
    amount: float
    currency: str = "INR"
    status: PaymentStatusEnum = PaymentStatusEnum.pending
    reference: Optional[str] = None
    metadata: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeacherCreate(BaseModel):
    subjects: List[str] = []
    experience: Optional[int] = None
    qualifications: Optional[str] = None


class TeacherUpdate(BaseModel):
    subjects: Optional[List[str]] = None
    experience: Optional[int] = None
    qualifications: Optional[str] = None


class TeacherRead(BaseModel):
    id: int
    user_id: int
    subjects: List[str] = []
    experience: Optional[int] = None
    qualifications: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EnrollmentCreate(BaseModel):
    batch_id: int
    role_in_batch: Optional[str] = "student"

class EnrollmentUpdate(BaseModel):
    is_active: Optional[bool] = None
    role_in_batch: Optional[str] = None

class EnrollmentRead(BaseModel):
    id: int
    batch_id: int
    student_id: int
    joined_at: datetime
    is_active: bool
    role_in_batch: str

    model_config = ConfigDict(from_attributes=True)

class StudentRead(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: Optional[str] = None
    enrollments: List[EnrollmentRead] = []

    model_config = ConfigDict(from_attributes=True)    


class ContentRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    content_type: Optional[str] = None
    storage_url: str
    uploader_id: int
    batch_id: Optional[int] = None
    created_at: datetime
    is_public: bool = False

    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    text: str


class CommentRead(BaseModel):
    id: int
    content_id: int
    author_id: int
    text: str
    created_at: datetime
    is_public: bool = True

    model_config = ConfigDict(from_attributes=True)    


class NotificationCreate(BaseModel):
   
    recipient_id: Optional[int] = None
    batch_id: Optional[int] = None
    title: Optional[str] = None
    message: str
    channel: Optional[str] = "in-app" 
    is_public: Optional[bool] = False


class NotificationRead(BaseModel):
    id: int
    recipient_id: int
    title: Optional[str] = None
    message: str
    channel: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SlotCreate(BaseModel):
    teacher_id: int
    class_id: int
    subject_id: int
    day: str
    start_time: str
    end_time: str


class SlotUpdate(BaseModel):
    teacher_id: Optional[int] = None
    class_id: Optional[int] = None
    subject_id: Optional[int] = None
    day: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class SlotRead(BaseModel):
    id: int
    teacher_id: int
    class_id: int
    subject_id: int
    day: str
    start_time: str
    end_time: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)