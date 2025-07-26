import re
from typing import Any, Optional

from options.enums import ProductType, Sex, product_type_mapping_table, sex_mapping_table

EXPIRY = int
DURATION = int


class UserState:
    def __init__(self):
        self.custom_name: str = "홍길동"
        self.insu_age: Optional[int] = 25
        self.insu_sex: Optional[Sex] = Sex.MALE
        self.product_type: Optional[ProductType] = ProductType.NON_REFUND
        self.expiry: int = 20
        self.duration: int = 100

    def __repr__(self) -> str:
        sex = sex_mapping_table[Sex.MALE] if self.insu_sex == Sex.MALE else sex_mapping_table[Sex.FEMALE]
        product_type = "무해지형" if self.product_type == ProductType.NON_REFUND else "해지환급형"
        return (
            "\n=== 실행 결과 ===\n"
            "\n[설정값]\n"
            f"이름: {self.custom_name}\n"
            f"나이: {self.insu_age}세\n"
            f"성별: {sex}\n"
            f"상품유형: {product_type}\n"
            f"보험기간: {self.expiry_year}"
        )

    @property
    def expiry_year(self) -> str:
        return f"{self.expiry}y_{self.duration}"

    @classmethod
    def extract_age(cls, user_input: str) -> Any:
        age_match = re.search(r"(\d+)세", user_input)
        if age_match:
            return int(age_match.group(1))

    @classmethod
    def extract_sex(cls, user_input: str) -> Any:
        if re.search(r"(남성|남자)", user_input):
            return Sex.MALE
        if re.search(r"(여성|여자)", user_input):
            return Sex.FEMALE

    @classmethod
    def extract_product_type(cls, user_input: str) -> Any:
        if product_type_mapping_table[ProductType.NON_REFUND] in user_input:
            return ProductType.NON_REFUND
        if product_type_mapping_table[ProductType.REFUND] in user_input:
            return ProductType.REFUND

    @classmethod
    def extract_expiry_and_duration(
        cls,
        user_input: str,
        expiry: int = 20,
        duration: int = 100,
    ) -> tuple[EXPIRY, DURATION]:
        period_match = re.search(r"(\d+)년[/\s](\d+)세", user_input)
        if period_match:
            expiry = int(period_match.group(1))
            duration = int(period_match.group(2))
            return expiry, duration
        return expiry, duration

    @classmethod
    def update_by_user_input_none(cls, instance: "UserState", user_input: str) -> "UserState":
        age = cls.extract_age(user_input)
        if age is not None:
            instance.insu_age = age

        sex = cls.extract_sex(user_input)
        if sex is not None:
            instance.insu_sex = sex

        product_type = cls.extract_product_type(user_input)
        if product_type is not None:
            instance.product_type = product_type

        expiry, duration = cls.extract_expiry_and_duration(user_input)
        if expiry is not None:
            instance.expiry = expiry

        if duration is not None:
            instance.duration = duration

        return instance
