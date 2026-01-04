"""
数据库管理模块
负责数据库连接和会话管理
"""

import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import Field, SQLModel

from ..api.miit import QueryResult
from .config import DatabaseConfig

logger = logging.getLogger(__name__)


# {
#       "contentTypeName": "广播电影电视节目",
#       "domain": "bilibili.com",
#       "domainId": 110000731411,
#       "leaderName": "",
#       "limitAccess": "否",
#       "mainId": 230000170723,
#       "mainLicence": "沪ICP备13002172号",
#       "natureName": "企业",
#       "serviceId": 110000507416,
#       "serviceLicence": "沪ICP备13002172号-3",
#       "unitName": "上海宽娱数码科技有限公司",
#       "updateRecordTime": "2025-10-09 16:00:40"
#     }
class IcpRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    domain: str = Field(index=True, description="域名")
    unit_name: str = Field(description="单位名称")
    main_licence: str = Field(description="主备案号")
    service_licence: str = Field(description="服务备案号")
    content_type_name: str | None = Field(description="内容类型名称", default=None)
    nature_name: str = Field(description="性质名称")
    leader_name: str | None = Field(description="负责人名称")
    limit_access: bool = Field(description="是否限制访问")
    main_id: int | None = Field(description="主备案ID")
    service_id: int | None = Field(description="服务备案ID", default=None)
    update_record_time: datetime = Field(description="备案更新时间")

    @staticmethod
    def from_query_result(result: QueryResult):
        return IcpRecord(
            domain=result.domain,
            unit_name=result.unitName,
            main_licence=result.mainLicence,
            service_licence=result.serviceLicence,
            content_type_name=result.contentTypeName,
            nature_name=result.natureName,
            leader_name=result.leaderName,
            limit_access=result.limitAccess != "否",
            main_id=result.mainId,
            service_id=result.serviceId,
            update_record_time=datetime.strptime(
                result.updateRecordTime, "%Y-%m-%d %H:%M:%S"
            ),
        )


engine: AsyncEngine | None = None


async def init_db(config: DatabaseConfig):
    global engine
    engine = create_async_engine(
        config.dsn,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


def get_engine() -> AsyncEngine:
    if engine is None:
        raise ValueError("数据库引擎尚未初始化，请先调用 init_db()")
    return engine
