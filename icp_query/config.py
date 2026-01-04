"""
配置管理模块
负责加载和管理应用配置
"""

import logging
import sys

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from .db.config import DatabaseConfig

logger = logging.getLogger(__name__)


class LoggingConfig(BaseModel):
    """日志配置"""

    level: str = Field("INFO", description="日志级别")


class ConfigManager(BaseSettings):
    """配置管理器"""

    model_config = SettingsConfigDict(
        env_nested_delimiter="__", yaml_file="config.yaml"
    )

    env: str = Field("development", description="运行环境")

    logging: LoggingConfig
    database: DatabaseConfig

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
        )


def load_config() -> ConfigManager:
    """
    加载配置文件的便捷函数

    Args:
        config_file: 配置文件路径

    Returns:
        ConfigManager 实例
    """
    try:
        cm = ConfigManager()  # type: ignore
        return cm
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        print(f"错误: {e}")
        sys.exit(1)
