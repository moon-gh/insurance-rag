from pathlib import Path
from enum import IntEnum
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
# print(f"{PROJECT_ROOT=}")


class Sex(IntEnum):
    FEMALE = 2  # 여자
    MALE = 1  # 남자


@dataclass
class PersonConfig:
    custom_name: str
    insu_age: int
    sex: Sex
    product_type: str
    expiry_year: str
    expiry: int
    duration: int


# @dataclass
# class DBConfig:
#     host: str
#     user: str
#     password: str
#     database: str


# # 데이터베이스 연결 설정
# DB_CONFIG = DBConfig(
#     host="localhost",
#     user="root",
#     password="12345678",
#     database="insu",
# )

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "12345678",
    "database": "insu",
}

# 기본 설정값 추가
DEFAULT_CONFIG = PersonConfig(
    custom_name="홍길동",
    insu_age=25,
    sex=Sex.MALE,
    product_type="nr",  # nr: 무해지형, r: 해지환급형
    expiry_year="20y_100",
    expiry=20,
    duration=100,
)
