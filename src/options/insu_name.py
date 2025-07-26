from typing import TypedDict


class InsuMatch(TypedDict):
    DB손해보험: str
    삼성화재: str
    하나손해보험: str
    한화손해보험: str
    흥국화재: str
    현대해상: str
    KB손해보험: str
    롯데손해보험: str
    MG손해보험: str
    메리츠화재: str
    NH농협손해보험: str


insu_match: InsuMatch = {
    "DB손해보험": "DBSonBo_YakMu20250123",
    "삼성화재": "Samsung_YakMu2404103NapHae20250113",
    "하나손해보험": "HaNa_YakMuHaGaengPyo20250101",
    "한화손해보험": "HanWha_YakHan20250201",
    "흥국화재": "Heung_YakMu250220250205",
    "현대해상": "HyunDai_YakMuSeH1Il2Nap20250213",
    "KB손해보험": "KB_YakKSeHaeMu250120250214",
    "롯데손해보험": "LotteSonBo_YakMuLDeo25011220250101",
    "MG손해보험": "MGSonBo_YakMuWon2404Se20250101",
    "메리츠화재": "Meritz_YakMu220250113",
    "NH농협손해보험": "NH_YakMuN5250120250101",
}

nh_keywords = ["NH농협손해보험", "NH손해보험", "농협손해보험", "NH손보", "농협손보", "NH", "농협"]
db_keywords = ["db손해보험", "db손해", "db보험", "db", "디비손해보험", "디비"]
