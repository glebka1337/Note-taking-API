import re
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy import delete, select
from api.core.models import Note, CrossLink, note_tags
from sqlalchemy.orm import selectinload

class NoteDeleteService:
    """
    A service class for handling the deletion of notes and all associated data.
    """
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        # A set to track note IDs during a recursive deletion to prevent infinite loops in case of a bug.
        self._deletion_path = set()

    async def _find_notes_with_links_to(self, note_id: int) -> list[Note]:
        """
        Retrieves all notes that contain a CrossLink pointing to the given note ID.
        This is a helper method to find notes that need their content updated.

        Args:
            note_id (int): The ID of the note to which other notes are linked.

        Returns:
            list[Note]: A list of Note ORM objects that link to the specified note.
        """
        # We use a JOIN to find notes that have a CrossLink record pointing to the target note.
        stmt = (
            select(Note)
            .join(CrossLink, Note.id == CrossLink.note_id)
            .where(CrossLink.linked_note_id == note_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _replace_deleted_links_in_content(
        self,
        notes_to_update: list[Note],
        deleted_note_uuid: UUID,
        placeholder_text: str
    ):
        """
        Updates the content of a list of notes by replacing Markdown links
        to the deleted note with a placeholder text.

        Args:
            notes_to_update (list[Note]): The notes whose content needs to be updated.
            deleted_note_uuid (UUID): The UUID of the note that is being deleted.
            placeholder_text (str): The text to replace the link with.
        """
        # Regex to find links in the format [Title](UUID) that match the specific UUID.
        link_pattern = re.compile(f"\\[.*?\\]\\({deleted_note_uuid}\\)")
        
        for note in notes_to_update:
            original_content = note.content
            
            # The re.sub() function performs the replacement.
            new_content = link_pattern.sub(f"[{placeholder_text}]", original_content)
            
            # Update the note and flush the session to commit the content change.
            if new_content != original_content:
                note.content = new_content
                self.db.add(note)
                await self.db.flush()

    async def _delete_note_recursively(self, note: Note):
        """
        A private, recursive helper method to delete a note and all of its descendants,
        ensuring all related entities are handled correctly.

        Args:
            note (Note): The note ORM object to be deleted.
        """
        # Add the note's ID to the set to prevent infinite recursion.
        if note.id in self._deletion_path:
            return  # Already in the deletion path, so we exit.
        self._deletion_path.add(note.id)
        
        # 1. Recursively delete all child notes first.
        children_result = await self.db.execute(
            select(Note).where(Note.parent_id == note.id).options(selectinload(Note.children))
        )
        children = children_result.scalars().all()
        
        for child in children:
            await self._delete_note_recursively(child)
        
        # 2. Before deleting, find and update all notes that contain links to this note.
        notes_with_links = await self._find_notes_with_links_to(note.id)
        
        await self._replace_deleted_links_in_content(
            notes_with_links,
            note.uuid,
            placeholder_text=f"DELETED: {note.title}"
        )
        
        # 3. Handle all related database entities.
        # It's cleaner and safer to handle these explicitly than relying on cascade options.
        
        # Delete associations in the many-to-many "note_tags" table.
        await self.db.execute(delete(note_tags).where(note_tags.c.note_id == note.id))
        
        # Delete "forward" links (from this note to others).
        await self.db.execute(delete(CrossLink).where(CrossLink.note_id == note.id))
        
        # Delete "backward" links (from other notes to this note).
        await self.db.execute(delete(CrossLink).where(CrossLink.linked_note_id == note.id))

        # 4. Finally, delete the note itself.
        await self.db.delete(note)
        await self.db.flush() # Flushes the current changes to the database.

    async def delete_note(self, note_to_delete: Note):
        """
        The main public method to initiate the note deletion process.
        It starts a database transaction and handles the top-level note.

        Args:
            note_to_delete (Note): The note ORM object to be deleted.
        """
            
        try:
            await self._delete_note_recursively(note_to_delete)
            await self.db.commit() 
        except Exception as e:
            await self.db.rollback() # Roll back the transaction on any error.
            raise e