from pathlib import Path

from types.enum import Sex, ProductType

from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


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
