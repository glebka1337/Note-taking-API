from uuid import uuid4
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
        Updates children of the note. If there are no children, all links to children are deleted.
        Otherwise, it takes the list of children titles, and:
        - If the title doesn't exist as a child, it creates a new note with this title and links to it.
        - If the title already exists as a child, it creates a new title by appending a counter to the end
          of the title.
        """
        if not self.parsed_children:
            await self.db.execute(
                update(Note)
                .where(Note.parent_id == self.note.id)
                .values(parent_id=None)
            )
            return

        result = await self.db.execute(
            select(Note.title).where(
                Note.user_id == self.note.user_id, 
                Note.parent_id == self.note.id
            )
        )
        existing_titles = {title for (title,) in result.all()}

        for child_title in self.parsed_children:
            new_title = child_title
            counter = 2
            
            while new_title in existing_titles:
                new_title = f"{child_title} ({counter})"
                counter += 1

            new_child = Note(
                title=new_title,
                content="",
                user_id=self.note.user_id,
                parent_id=self.note.id,
                uuid=str(uuid4())
            )
            self.db.add(new_child)
            existing_titles.add(new_title)

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