"""Email repository for database operations."""

from datetime import datetime

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Email


class EmailRepository:
    """Repository for Email database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        gmail_id: str,
        sender_name: str | None = None,
        sender_email: str | None = None,
        subject: str | None = None,
        body_html: str | None = None,
        body_text: str | None = None,
        email_date: datetime | None = None,
    ) -> Email:
        """Create a new email record."""
        email = Email(
            gmail_id=gmail_id,
            sender_name=sender_name,
            sender_email=sender_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            email_date=email_date,
        )
        self.session.add(email)
        await self.session.commit()
        await self.session.refresh(email)
        return email

    async def get_by_gmail_id(self, gmail_id: str) -> Email | None:
        """Get email by Gmail message ID."""
        result = await self.session.execute(
            select(Email).where(Email.gmail_id == gmail_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, email_id: int) -> Email | None:
        """Get email by database ID."""
        result = await self.session.execute(select(Email).where(Email.id == email_id))
        return result.scalar_one_or_none()

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        allowed_domains: list[str] | None = None,
    ) -> list[Email]:
        """Get emails within a date range, optionally filtered by sender domain."""
        query = (
            select(Email)
            .where(Email.email_date >= start_date)
            .where(Email.email_date < end_date)
        )
        if allowed_domains:
            domain_filters = [
                Email.sender_email.contains(domain) for domain in allowed_domains
            ]
            query = query.where(or_(*domain_filters))
        result = await self.session.execute(query.order_by(Email.email_date.asc()))
        return list(result.scalars().all())

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[Email]:
        """Get all emails with pagination."""
        result = await self.session.execute(
            select(Email).order_by(Email.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def exists(self, gmail_id: str) -> bool:
        """Check if email exists by Gmail ID."""
        email = await self.get_by_gmail_id(gmail_id)
        return email is not None

    async def create_if_not_exists(
        self,
        gmail_id: str,
        sender_name: str | None = None,
        sender_email: str | None = None,
        subject: str | None = None,
        body_html: str | None = None,
        body_text: str | None = None,
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
            body_html=body_html,
            body_text=body_text,
            email_date=email_date,
        )
        return email, True
