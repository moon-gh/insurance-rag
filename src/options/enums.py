from enum import IntEnum, StrEnum


class Sex(IntEnum):
    FEMALE = 0  # 여자
    MALE = 1  # 남자


class ProductType(StrEnum):
    NON_REFUND = "nr"  # 무해지환급형
    REFUND = "r"  # 해지환급형


class IntentType(StrEnum):
    COMPARE_QUESTION = "비교설계 질문"
    POLICY_QUESTION = "보험약관 질문"


class ConversationFlow(StrEnum):
    ENTRY = "entry"
    INTENT = "intent"
    RESULT = "result"
    END = "end"


class ModelType(StrEnum):
    INTENT_MODEL = "gpt-4-turbo"


CompanyName = str
CompanyRelevanceText = str
CompanyNameRelevanceTextPair = dict[CompanyName, CompanyRelevanceText]
