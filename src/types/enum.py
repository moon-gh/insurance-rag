from enum import IntEnum, StrEnum


class Sex(IntEnum):
    FEMALE = 2  # 여자
    MALE = 1  # 남자


class ProductType(StrEnum):
    NON_REFUND = "nr"  # 무해지환급형
    REFUND = "r"  # 해지환급형
