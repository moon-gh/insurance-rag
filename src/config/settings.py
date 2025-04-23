import os
from pathlib import Path

from options.enums import Sex, ProductType

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()
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
    db_password: str = os.environ["DB_PASSWORD"]
    db_database: str = "insu"

    vector_path: str = "insu_data"
    openai_api_key: str = os.environ["OPENAI_API_KEY"]
    upstage_api_key: str = os.environ["UPSTAGE_API_KEY"]


settings = Settings()
