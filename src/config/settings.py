import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

from options.enums import ServiceEnv

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def get_env_file_name(env: Optional[str]) -> str:
    if not env or env.upper() not in ServiceEnv._value2member_map_:
        return ""
    return f".{env.lower()}"


class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: str = "3306"
    db_user: str = "root"
    db_password: str
    db_database: str = "insu"

    vector_path: str = "insu_data"
    openai_api_key: str
    upstage_api_key: str

    model_config = SettingsConfigDict(
        env_file=f"{PROJECT_ROOT}/{get_env_file_name(os.environ['CONF_ENV'])}.env", env_file_encoding="utf-8"
    )


settings = Settings()
