from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import comments, contents
from app.schema import CommentCreate, CommentRead
from app.core.authen import get_current_user

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/", response_model=CommentRead)
def add_comment(
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    content = db.query(contents).filter(contents.id == payload.content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    row = comments(
        content_id=payload.content_id,
        author_id=current_user.id,
        text=payload.text
    )

    db.add(row)
    db.commit()
    db.refresh(row)
    return CommentRead.model_validate(row)


@router.get("/content/{content_id}", response_model=List[CommentRead])
def get_comments_by_content(
    content_id: int,
    db: Session = Depends(get_db)
):
    content = db.query(contents).filter(contents.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    rows = db.query(comments).filter(
        comments.content_id == content_id,
        comments.is_public == True
    ).order_by(comments.created_at).all()

    return [CommentRead.model_validate(r) for r in rows]
