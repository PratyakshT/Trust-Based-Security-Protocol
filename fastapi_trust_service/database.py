# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

# Connect to the exact same database Django created.
# Notice the "+asyncpg" driver for high-speed asynchronous I/O.
DATABASE_URL = "postgresql+asyncpg://postgres:[PASSWORD]@localhost:5432/siot_network"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Dependency to get DB session per request
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session