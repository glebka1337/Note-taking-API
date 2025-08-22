from sqlalchemy.ext.asyncio import AsyncSession
from api.core.models import Note


class NoteService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    def parse_and_create(self, note: Note, parsed_tags: list[str], parsed_children: list[str], parsed_links: list[dict]):
        self._handle_tags(note, parsed_tags)
        self._handle_children(note, parsed_children)
        self._handle_links(note, parsed_links)
        self.db.commit()

    def _handle_tags(self, note, tags):
        pass

    def _handle_children(self, note, children_titles):
        pass

    def _handle_links(self, note, links):
        pass
