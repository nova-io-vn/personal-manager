from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.belonging import PersonalItem
from app.schemas.belonging import PersonalItemCreate, PersonalItemRead, PersonalItemUpdate

router = APIRouter(prefix="/belongings", tags=["belongings"])


@router.get("", response_model=list[PersonalItemRead])
def list_items(category: str | None = None, db: Session = Depends(get_db)):
    query = select(PersonalItem).order_by(PersonalItem.category, PersonalItem.name)
    if category:
        query = query.where(PersonalItem.category == category)
    return list(db.scalars(query).all())


@router.post("", response_model=PersonalItemRead, status_code=201)
def create_item(data: PersonalItemCreate, db: Session = Depends(get_db)):
    item = PersonalItem(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=PersonalItemRead)
def update_item(item_id: int, data: PersonalItemUpdate, db: Session = Depends(get_db)):
    item = db.get(PersonalItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Personal item not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(PersonalItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Personal item not found")
    db.delete(item)
    db.commit()
    return Response(status_code=204)
