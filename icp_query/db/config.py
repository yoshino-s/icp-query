from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """数据库配置（使用 DSN）"""

    dsn: str = Field(
        ...,
        description=(
            "数据库连接 DSN，例如：postgresql+psycopg2://user:password@host:5432/database"
        ),
    )
    pool_size: int = Field(5, ge=1, description="连接池大小")
    max_overflow: int = Field(10, ge=0, description="连接池最大溢出")
