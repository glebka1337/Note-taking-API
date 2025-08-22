from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, BigInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from api.core.db import Base
from sqlalchemy import Table
from uuid import uuid4, UUID

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    notes: Mapped[list["Note"]] = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    tags: Mapped[list["Tag"]] = relationship("Tag", back_populates="user", cascade="all, delete-orphan")

class CrossLink(Base):
    __tablename__ = "cross_links"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False) 
    
    note_id: Mapped[int] = mapped_column(ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    linked_note_id: Mapped[int] = mapped_column(ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    
    note: Mapped["Note"] = relationship("Note", foreign_keys=[note_id], back_populates="linked_notes")
    linked_note: Mapped["Note"] = relationship("Note", foreign_keys=[linked_note_id], back_populates="backlinks")

class Note(Base):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        default=uuid4,
        unique=True,
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False) 
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="notes")
    
    parent_id: Mapped[int] = mapped_column(ForeignKey("notes.id", ondelete="CASCADE"), nullable=True)
    parent: Mapped["Note"] = relationship("Note", remote_side=[id], back_populates="children")
    children: Mapped[list["Note"]] = relationship("Note", back_populates="parent", cascade="all, delete-orphan")
    
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary="note_tags",
        back_populates="notes"
    )
    
    linked_notes: Mapped[list["CrossLink"]] = relationship(
        "CrossLink",
        foreign_keys="[CrossLink.note_id]",
        back_populates="note",
        cascade="all, delete-orphan"
    )
    
    backlinks: Mapped[list["CrossLink"]] = relationship(
        "CrossLink",
        foreign_keys="[CrossLink.linked_note_id]",
        back_populates="linked_note",
        cascade="all, delete-orphan"
    )
    

class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_tag_user_name"),)
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False) 
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="tags")
    
    notes: Mapped[list["Note"]] = relationship(
        "Note",
        secondary="note_tags",
        back_populates="tags"
    )

note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)