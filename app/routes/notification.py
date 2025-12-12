from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import notifications, users, enrollments, batches  
from app.schema import NotificationCreate, NotificationRead
from app.core.authen import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _is_admin(user) -> bool:
    return getattr(user, "is_admin", False) or getattr(user, "role", "") == "admin"


def _is_coordinator(user) -> bool:
    return getattr(user, "role", "") == "coordinator"


def _is_teacher(user) -> bool:
    return getattr(user, "role", "") == "teacher"


@router.post("/", response_model=List[NotificationRead], status_code=status.HTTP_201_CREATED)
def send_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):

    if not (_is_admin(current_user) or _is_coordinator(current_user) or _is_teacher(current_user)):
        raise HTTPException(status_code=403, detail="Only admin/coordinator/teacher can send notifications")

    if not payload.recipient_id and not payload.batch_id:
        raise HTTPException(status_code=400, detail="recipient_id or batch_id is required")

    created_notifications = []

    if payload.recipient_id:
   
        recipient = db.query(users).filter(users.id == payload.recipient_id).first()
        if not recipient:
            raise HTTPException(status_code=404, detail="Recipient user not found")

        n = notifications(
            recipient_id=payload.recipient_id,
            title=payload.title,
            message=payload.message,
            channel=payload.channel or "in-app",
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.add(n)
        db.commit()
        db.refresh(n)
        created_notifications.append(n)
        return [NotificationRead.model_validate(n) for n in created_notifications]

    if payload.batch_id:
        batch = db.query(batches).filter(batches.id == payload.batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")

        if _is_coordinator(current_user) and batch.coordinator_id is not None:
            if batch.coordinator_id != current_user.id and not _is_admin(current_user):
                raise HTTPException(status_code=403, detail="Coordinator can send only to their own batch")

        enroll_rows = db.query(enrollments).filter(
            enrollments.batch_id == payload.batch_id,
            enrollments.is_active == True
        ).all()

        if not enroll_rows:
            return []

        for e in enroll_rows:
            n = notifications(
                recipient_id=e.student_id,
                title=payload.title,
                message=payload.message,
                channel=payload.channel or "in-app",
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.add(n)
            created_notifications.append(n)

        db.commit()
        for n in created_notifications:
            db.refresh(n)

        return [NotificationRead.model_validate(n) for n in created_notifications]


@router.get("/me", response_model=List[NotificationRead])
def list_my_notifications(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    limit: int = 100
):

    q = db.query(notifications).filter(notifications.recipient_id == current_user.id).order_by(notifications.created_at.desc()).limit(limit)
    rows = q.all()
    return [NotificationRead.model_validate(r) for r in rows]


@router.put("/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):

    n = db.query(notifications).filter(notifications.id == notification_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")

    if not (_is_admin(current_user) or n.recipient_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    n.is_read = True
    db.add(n)
    db.commit()
    db.refresh(n)
    return NotificationRead.model_validate(n)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):

    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admin can delete notifications")

    n = db.query(notifications).filter(notifications.id == notification_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")

    db.delete(n)
    db.commit()
    return None
