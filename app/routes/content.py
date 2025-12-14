from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import contents, comments,users, enrollments, batches  
from app.schema import ContentRead, CommentCreate, CommentRead
from app.core.authen import get_current_user
from app.models.models import ContentTypeEnum


router = APIRouter(prefix="/contents", tags=["contents"])

def _user_is_enrolled(db: Session, user_id: int, batch_id: int) -> bool:
    
    if batch_id is None:
        return True
    e = db.query(enrollments).filter(
        enrollments.batch_id == batch_id,
        enrollments.student_id == user_id,
        enrollments.is_active == True
    ).first()
    return bool(e)

def _is_teacher(user):
    return getattr(user, "role", "") == "teacher"

def _is_admin(user):
    return getattr(user, "role", "") == "admin"


@router.post("/", response_model=ContentRead)
def upload_content(
    title: str,
    storage_url: str,
    description: str = "",
    content_type: str = "video",
    batch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    
    if not (_is_teacher(current_user) or _is_admin(current_user)):
        raise HTTPException(status_code=403, detail="Not allowed to upload content")

    if batch_id is not None:
        batch = db.query(batches).filter(batches.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")

    new_content = contents(
    title=title,
    description=description,
    storage_url=storage_url,
    content_type=ContentTypeEnum(content_type),
    uploader_id=current_user.id,
    batch_id=batch_id,
)

    db.add(new_content)
    db.commit()
    db.refresh(new_content)

    return ContentRead.model_validate(new_content)

@router.get("/", response_model=List[ContentRead])
def list_contents(batch_id: Optional[int] = None, only_public: Optional[bool] = False, db: Session = Depends(get_db)):

    q = db.query(contents)
    if batch_id is not None:
        q = q.filter(contents.batch_id == batch_id)
    if only_public:
        q = q.filter(contents.is_public == True)
    rows = q.order_by(contents.created_at.desc()).all()
    return [ContentRead.model_validate(r) for r in rows]


@router.get("/{content_id}", response_model=ContentRead)
def get_content(content_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):

    row = db.query(contents).filter(contents.id == content_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Content not found")

    if row.batch_id is not None:
        
        if current_user is None:
            raise HTTPException(status_code=403, detail="Authentication required to view this content")
        if not _user_is_enrolled(db, current_user.id, row.batch_id) and not getattr(current_user, "is_admin", False):
            raise HTTPException(status_code=403, detail="Not enrolled in this batch")

    return ContentRead.model_validate(row)


@router.get("/{content_id}/comments", response_model=List[CommentRead])
def list_comments(content_id: int, db: Session = Depends(get_db)):

    row = db.query(contents).filter(contents.id == content_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Content not found")

    crows = db.query(comments).filter(comments.content_id == content_id, comments.is_public == True).order_by(comments.created_at.asc()).all()
    return [CommentRead.model_validate(c) for c in crows]


@router.post("/{content_id}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
def create_comment(content_id: int, payload: CommentCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):

    row = db.query(contents).filter(contents.id == content_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Content not found")

    if row.batch_id is not None:
        if not _user_is_enrolled(db, current_user.id, row.batch_id) and not getattr(current_user, "is_admin", False):
            raise HTTPException(status_code=403, detail="Not enrolled in this batch")

    comment_row = comments(
        content_id=content_id,
        author_id=current_user.id,
        text=payload.text,
    )
    db.add(comment_row)
    db.commit()
    db.refresh(comment_row)
    return CommentRead.model_validate(comment_row)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):

    c = db.query(comments).filter(comments.id == comment_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Comment not found")

    if not (getattr(current_user, "is_admin", False) or c.author_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

    db.delete(c)
    db.commit()
    return None
