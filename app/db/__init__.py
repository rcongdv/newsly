from app.db.database import get_database
from app.db.repositories.email import EmailRepository

__all__ = [
    "get_database",
    "EmailRepository",
]
