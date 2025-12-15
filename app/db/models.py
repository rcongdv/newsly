from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    gmail_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    sender_name: Mapped[str | None] = mapped_column(String(500))
    sender_email: Mapped[str | None] = mapped_column(String(500))
    subject: Mapped[str | None] = mapped_column(String(1000))
    snippet: Mapped[str | None] = mapped_column(Text)
    body_html: Mapped[str | None] = mapped_column(Text)
    body_text: Mapped[str | None] = mapped_column(Text)
    email_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    def __repr__(self) -> str:
        return (
            f"<Email(id={self.id}, gmail_id={self.gmail_id}, subject={self.subject})>"
        )
