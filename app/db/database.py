import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class Database:

    def __init__(self):
        settings = get_settings()
        database_url = settings.database_url

        # Convert postgres:// to postgresql+asyncpg:// for SQLAlchemy async
        if database_url.startswith("postgres://"):
            database_url = database_url.replace(
                "postgres://", "postgresql+asyncpg://", 1
            )
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )

        connect_args = {"command_timeout": 60}

        self.engine = create_async_engine(
            database_url,
            echo=False,
            connect_args=connect_args,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
        )
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self, max_retries: int = 5, retry_delay: float = 2.0):
        for attempt in range(max_retries):
            try:
                async with self.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Database connection attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {retry_delay}s..."
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 1.5
                else:
                    logger.error(
                        f"Failed to connect to database after {max_retries} attempts"
                    )
                    raise

    def get_session(self) -> async_sessionmaker[AsyncSession]:
        return self.async_session


_database: Database | None = None


def get_database() -> Database:
    global _database
    if _database is None:
        _database = Database()
    return _database
