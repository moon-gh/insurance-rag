from pathlib import Path
from enum import IntEnum, StrEnum
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


class Sex(IntEnum):
    FEMALE = 2  # 여자
    MALE = 1  # 남자


class ProductType(StrEnum):
    NON_REFUND = "nr"  # 무해지환급형
    REFUND = "r"  # 해지환급형


class Settings(BaseSettings):
    custom_name: str = "홍길동"
    insu_age: int = 25
    sex: Sex = Sex.MALE
    product_type: ProductType = ProductType.NON_REFUND
    expiry_year: str = "20y_100"
    expiry: int = 20
    duration: int = 100

    db_host: str = "localhost"
    db_port: str = "3306"
    db_user: str = "root"
    db_password: str = "12345678"  # TODO: env로 빼기
    db_database: str = "insu"


settings = Settings()
