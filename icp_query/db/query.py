import logging

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .db import IcpRecord

logger = logging.getLogger(__name__)


class Query:
    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def get(self, domain: str):
        async with AsyncSession(self.engine) as session:
            statement = select(IcpRecord).where(IcpRecord.domain == domain)
            result = await session.exec(statement)
            return result.first()

    async def save(self, record: IcpRecord):
        async with AsyncSession(self.engine) as session:
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record
