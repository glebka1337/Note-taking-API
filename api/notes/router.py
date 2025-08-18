from fastapi import APIRouter, Depends, status, HTTPException
from api.notes.schemas import NoteRead, NoteCreate, NoteUpdate
from api.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from api.models import Note, Tag
from sqlalchemy import select
from api.notes.utils import get_note_by_id, attach_tags

router = APIRouter(
    prefix="/notes",
    tags=["notes"],
)


@router.post('/', response_model=NoteRead)
async def create_new_note(
    note_in: NoteCreate, 
    db: AsyncSession = Depends(get_session)
):
    
    note_in_db_record = await db.execute(
        select(Note).where(Note.title == note_in.title)
    )
    
    if note_in_db_record.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note with this title already exists"
        )
    
    # создаём заметку
    note_data = note_in.model_dump()
    tag_ids = note_data.pop("tag_ids", [])
    note = Note(**note_data)

    # привязка тегов, если переданы
    if tag_ids:
        tags = await db.execute(select(Tag).where(Tag.id.in_(tag_ids)))
        note.tags = tags.scalars().all()

    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


# ==========================
# Получение списка заметок
# ==========================
@router.get('/', response_model=list[NoteRead])
async def get_notes(db: AsyncSession = Depends(get_session)):
    notes = await db.execute(select(Note))
    return notes.scalars().all()


# ==========================
# Получение одной заметки
# ==========================
@router.get('/{note_id}', response_model=NoteRead)
async def get_note(note_id: int, db: AsyncSession = Depends(get_session)):
    note = await get_note_by_id(note_id, db)
    return note


# ==========================
# Удаление заметки
# ==========================
@router.delete('/{note_id}')
async def delete_note(note_id: int, db: AsyncSession = Depends(get_session)):
    note = await get_note_by_id(note_id, db)
    await db.delete(note)
    await db.commit()
    return {"ok": True}


# ==========================
# Обновление заметки
# ==========================
@router.put('/{note_id}', response_model=NoteRead)
async def update_note(
    note_id: int,
    note_in: NoteUpdate,
    db: AsyncSession = Depends(get_session)
):
    note = await get_note_by_id(note_id, db)

    note_data = note_in.model_dump(exclude_unset=True)
    tag_ids = note_data.pop("tag_ids", None)

    for field, value in note_data.items():
        setattr(note, field, value)

    if tag_ids is not None:
        await attach_tags(note, tag_ids, db)

    await db.commit()
    await db.refresh(note)
    return note
