from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Email


class EmailRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        gmail_id: str,
        sender_name: str | None = None,
        sender_email: str | None = None,
        subject: str | None = None,
        snippet: str | None = None,
        body_html: str | None = None,
        body_text: str | None = None,
        ai_summary: str | None = None,
        email_date: datetime | None = None,
    ) -> Email:
        email = Email(
            gmail_id=gmail_id,
            sender_name=sender_name,
            sender_email=sender_email,
            subject=subject,
            snippet=snippet,
            body_html=body_html,
            body_text=body_text,
            ai_summary=ai_summary,
            email_date=email_date,
        )
        self.session.add(email)
        await self.session.commit()
        await self.session.refresh(email)
        return email

    async def get_by_gmail_id(self, gmail_id: str) -> Email | None:
        result = await self.session.execute(
            select(Email).where(Email.gmail_id == gmail_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, email_id: int) -> Email | None:
        result = await self.session.execute(select(Email).where(Email.id == email_id))
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[Email]:
        result = await self.session.execute(
            select(Email).order_by(Email.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def exists(self, gmail_id: str) -> bool:
        email = await self.get_by_gmail_id(gmail_id)
        return email is not None

    async def create_if_not_exists(
        self,
        gmail_id: str,
        sender_name: str | None = None,
        sender_email: str | None = None,
        subject: str | None = None,
        snippet: str | None = None,
        body_html: str | None = None,
        body_text: str | None = None,
        ai_summary: str | None = None,
        email_date: datetime | None = None,
    ) -> tuple[Email, bool]:
        """
        Create email if it doesn't exist.
        Returns tuple of (email, created) where created is True if new record was created.
        """
        existing = await self.get_by_gmail_id(gmail_id)
        if existing:
            return existing, False

        email = await self.create(
            gmail_id=gmail_id,
            sender_name=sender_name,
            sender_email=sender_email,
            subject=subject,
            snippet=snippet,
            body_html=body_html,
            body_text=body_text,
            ai_summary=ai_summary,
            email_date=email_date,
        )
        return email, True
