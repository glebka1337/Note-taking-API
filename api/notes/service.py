from uuid import uuid4
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from api.core.models import CrossLink, Note, Tag


class NoteService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def parse_and_create(self, note: Note, parsed_tags: list[str], parsed_children: list[str], parsed_links: list[dict]):
        self.note = note
        self.parsed_tags = parsed_tags
        self.parsed_children = parsed_children
        self.parsed_links = parsed_links
        

    async def _handle_tags(self):
        """
        Optimized handling of tags for a note:
        1. Checks which tags already exist in DB (by user_id + tag name)
        2. Creates missing tags
        3. Attaches all tags to the note
        """
        if not self.parsed_tags:
            self.note.tags = []
            return

        result = await self.db.execute(
            select(Tag).where(
                Tag.user_id == self.note.user_id,
                Tag.name.in_(self.parsed_tags)
            )
        )
        existing_tags = {tag.name: tag for tag in result.scalars().all()}

        tags_to_attach = []
        for tag_name in self.parsed_tags:
            if tag_name in existing_tags:
                tags_to_attach.append(existing_tags[tag_name])
            else:
                new_tag = Tag(name=tag_name, user_id=self.note.user_id)
                self.db.add(new_tag)
                tags_to_attach.append(new_tag)

        self.note.tags = tags_to_attach    
        
            
    async def _handle_children(self):
        """
        Creates and attaches child notes based on parsed children names.
        Ensures unique titles by appending a counter if necessary.
        """
        if not self.parsed_children:
            self.note.children = []
            return

        result = await self.db.execute(
            select(Note.title).where(Note.user_id == self.note.user_id, Note.parent_id == self.note.id)
        )
        existing_titles = {title for (title,) in result.all()}

        children_to_attach = []

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
            children_to_attach.append(new_child)
            existing_titles.add(new_title)  

        self.note.children = children_to_attach
        
    async def _handle_links(self):
        if not self.parsed_links:
            await self.db.execute(delete(CrossLink).where(CrossLink.note_id == self.note.id))
            return

        await self.db.execute(delete(CrossLink).where(CrossLink.note_id == self.note.id))

        result = await self.db.execute(
            select(Note).where(
                Note.uuid.in_(self.parsed_links.keys()),
                Note.user_id == self.note.user_id
            )
        )
        notes_found = result.scalars().all()

        links_to_create = [
            CrossLink(
                note_id=self.note.id,
                linked_note_id=note.id,
                title=self.parsed_links[note.uuid]
            )
            for note in notes_found
        ]

        if links_to_create:
            self.db.add_all(links_to_create)
