# api/notes/router.py

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.auth.schemas import UserOut
from api.auth.services.auth_service import get_current_user
from api.core.db import get_session
from api.core.models import Note, Tag
from api.notes.schemas import NoteRead, NoteCreate, NoteUpdate
from api.notes.utils import (
    get_note_by_id,
    attach_tags,
    update_note_cross_links,
    parse_inner_links,
)

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/", response_model=NoteRead)
async def create_note(
    note_in: NoteCreate,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):

    existing = await db.execute(
        select(Note).where(Note.title == note_in.title, Note.user_id == user.id)
    )
    if existing.scalar():
        raise HTTPException(400, "Note with this title already exists")

    note_data = note_in.model_dump()
    tag_ids = note_data.pop("tag_ids", [])
    note = Note(**note_data, user_id=user.id)

    if tag_ids:
        tags = await db.execute(select(Tag).where(Tag.id.in_(tag_ids)))
        note.tags = tags.scalars().all()

    db.add(note)
    await db.commit()
    await db.refresh(note)

    await update_note_cross_links(note, db)
    await db.commit()

    return note


@router.get("/", response_model=list[NoteRead])
async def get_notes(
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):
    result = await db.execute(select(Note).where(Note.user_id == user.id))
    return result.scalars().all()


@router.get("/{note_id}", response_model=NoteRead)
async def get_note(
    note_id: int,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):
    return await get_note_by_id(note_id, user.id, db)

@router.get("/{title}", response_model=NoteRead)
async def get_note_by_title(): ...

@router.put("/{note_id}", response_model=NoteRead)
async def update_note(
    note_id: int,
    note_in: NoteUpdate,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):
    note = await get_note_by_id(note_id, user.id, db)

    update_data = note_in.model_dump(exclude_unset=True)
    tag_ids = update_data.pop("tag_ids", None)

    for key, value in update_data.items():
        setattr(note, key, value)

    if tag_ids is not None:
        await attach_tags(note, tag_ids, db)

    await db.commit()
    await db.refresh(note)

    await update_note_cross_links(note, db)
    await db.commit()

    return note


@router.delete("/{note_id}")
async def delete_note(
    note_id: int,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):
    note = await get_note_by_id(note_id, user.id, db)
    await db.delete(note)
    await db.commit()
    return {"ok": True}

@router.get("/{note_id}/linked_notes")
async def get_linked_notes(
    note_id: int,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):
    note = await get_note_by_id(note_id, user.id, db)
    result = await db.execute(
        select(Note).where(Note.id.in_([n.id for n in note.linked_notes]))
    )
    notes = result.scalars().all()
    return [{"id": n.id, "slug": n.slug, "title": n.title} for n in notes]

@router.get("/{note_id}/backlinks")
async def get_backlinks(
    note_id: int,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):
    note = await get_note_by_id(note_id, user.id, db)
    result = await db.execute(
        select(Note).where(Note.id.in_([n.id for n in note.backlinks]))
    )
    notes = result.scalars().all()
    return [{"id": n.id, "slug": n.slug, "title": n.title} for n in notes]
