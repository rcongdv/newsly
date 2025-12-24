import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Database:

    def __init__(self):
        database_url = os.getenv("DATABASE_URL")

        # Convert postgres:// to postgresql+asyncpg:// for SQLAlchemy async
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        # For Fly.io internal connections, disable SSL
        connect_args = {}
        if os.getenv("FLY_APP"):
            # Running on Fly - use internal network without SSL
            connect_args["ssl"] = False

        self.engine = create_async_engine(
            database_url,
            echo=False,
            connect_args=connect_args,
            pool_pre_ping=True,
            pool_recycle=1800,
        )
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def get_session(self) -> async_sessionmaker[AsyncSession]:
        return self.async_session


_database: Database | None = None


def get_database() -> Database:
    global _database
    if _database is None:
        _database = Database()
    return _database
