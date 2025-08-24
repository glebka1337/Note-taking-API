from typing import List, Set
from uuid import uuid4
import uuid
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from api.core.models import CrossLink, Note, Tag, note_tags
from sqlalchemy.dialects.postgresql import insert as pg_insert

class NoteService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.note = None
        self.parsed_tags = []
        self.parsed_children = []
        self.parsed_links = []

    async def handle_note(self, note):
        self.note = note
        await self._handle_tags()
        await self._handle_children()
        await self._handle_links()

    async def _handle_tags(self):
        # Deletes all existing tags for the note and adds new ones based on parsed tags.
        await self.db.execute(
            note_tags.delete().where(note_tags.c.note_id == self.note.id)
        )
        
        # If there are no parsed tags, nothing more to do.
        if not self.parsed_tags:
            return
        
        # Get unique tags to avoid duplicate inserts
        unique_tags = list(set(self.parsed_tags))
        
        # Create tags
        tag_values = [{"name": name, "user_id": self.note.user_id} for name in unique_tags]
        
        # Insert tags
        stmt = pg_insert(Tag).values(tag_values).on_conflict_do_nothing()
        await self.db.execute(stmt)

        # Fetch tag IDs
        result = await self.db.execute(
            select(Tag.id, Tag.name).where(
                Tag.user_id == self.note.user_id,
                Tag.name.in_(unique_tags)
            )
        )
        
        # Map tag names to IDs
        tag_map = {name: id for id, name in result.all()}
        note_tag_values = [
            {"note_id": self.note.id, "tag_id": tag_map[tag_name]} 
            for tag_name in self.parsed_tags
            if tag_name in tag_map
        ]
        
        # Bulk insert note-tag associations
        if note_tag_values:
            await self.db.execute(note_tags.insert().values(note_tag_values))

    async def _handle_children(self):
        """
        Updates children relationships for a note.

        - Deletes any existing children that are no longer referenced in the new content.
        - Creates new notes for any new children titles referenced.
        """
        
        # 1. Получаем список всех существующих дочерних заметок
        existing_children_result = await self.db.execute(
            select(Note).where(Note.parent_id == self.note.id)
        )
        existing_children = existing_children_result.scalars().all()
        
        existing_titles = {child.title for child in existing_children}
        parsed_titles = set(self.parsed_children)
        
        # 2. Определяем заметки для удаления (те, что есть в БД, но нет в распарсенном контенте)
        titles_to_delete: Set[str] = existing_titles.difference(parsed_titles)
        
        if titles_to_delete:
            # Получаем UUID заметок для удаления
            notes_to_delete_result = await self.db.execute(
                select(Note.uuid).where(
                    Note.parent_id == self.note.id,
                    Note.title.in_(titles_to_delete)
                )
            )
            note_uuids_to_delete = notes_to_delete_result.scalars().all()
            
            # Удаляем заметки по UUID
            await self.db.execute(
                delete(Note).where(Note.uuid.in_(note_uuids_to_delete))
            )
            

        # 3. Находим "новые" дочерние заметки (те, что в контенте, но которых ещё нет в БД как дочерних)
        titles_to_create: Set[str] = parsed_titles.difference(existing_titles)
        
        # 4. Создаем новые заметки для каждого нового названия
        for child_title in titles_to_create:
            new_title = child_title
            counter = 2
            
            # Проверяем на уникальность заголовка
            while True:
                existing_note_check = await self.db.execute(
                    select(Note).where(
                        Note.title == new_title,
                        Note.user_id == self.note.user_id
                    )
                )
                if existing_note_check.scalar_one_or_none() is None:
                    break
                
                new_title = f"{child_title} ({counter})"
                counter += 1
                
            new_child = Note(
                title=new_title,
                content="",
                user_id=self.note.user_id,
                parent_id=self.note.id,
                uuid=str(uuid.uuid4())
            )
            self.db.add(new_child)

    async def _handle_links(self):
        """
        Updates cross-links for the current note.

        Deletes all cross-links for the current note, then creates new ones
        based on the parsed links. If a link doesn't point to an existing note,
        it's ignored.

        :return: None
        """
        await self.db.execute(
            delete(CrossLink).where(CrossLink.note_id == self.note.id)
        )
        
        if not self.parsed_links:
            return

        
        link_uuids = list(self.parsed_links.keys())
        result = await self.db.execute(
            select(Note.id, Note.uuid).where(
                Note.uuid.in_(link_uuids),
                Note.user_id == self.note.user_id
            )
        )
        note_map = {str(uuid): id for id, uuid in result.all()}

        links_to_create = []
        for link_uuid, link_title in self.parsed_links.items():
            if link_uuid in note_map:
                links_to_create.append(CrossLink(
                    note_id=self.note.id,
                    linked_note_id=note_map[link_uuid],
                    title=link_title or f"Link to {link_uuid}"
                ))

        if links_to_create:
            self.db.add_all(links_to_create)