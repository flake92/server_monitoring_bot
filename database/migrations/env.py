from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

connect_args = {}
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def run_migrations_online():
    async with engine.connect() as connection:
        await connection.run_sync(config.set_main_option, "sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
        await connection.run_sync(context.configure, connection=connection, target_metadata=target_metadata)
        async with context.begin_transaction():
            await connection.run_sync(context.run_migrations)