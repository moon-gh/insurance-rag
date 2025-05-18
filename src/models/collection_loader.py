import json
import os
from pathlib import Path

import faiss
from langchain.embeddings.base import Embeddings


class CollectionLoader:
    def __init__(self, vector_path: str, embeddings: Embeddings):
        self.base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), vector_path)
        self.embeddings = embeddings
        self.collections = []
        self.collection_to_company_mapping = {
            "DBSonBo_YakMu20250123": "DB손해보험",
            "Samsung_YakMu2404103NapHae20250113": "삼성화재",
            "HaNa_YakMuHaGaengPyo20250101": "하나손해보험",
            "HanWha_YakHan20250201": "한화손해보험",
            "Heung_YakMu250220250205": "흥국화재",
            "HyunDai_YakMuSeH1Il2Nap20250213": "현대해상",
            "KB_YakKSeHaeMu250120250214": "KB손해보험",
            "LotteSonBo_YakMuLDeo25011220250101": "롯데손해보험",
            "MGSonBo_YakMuWon2404Se20250101": "MG손해보험",
            "Meritz_YakMu220250113": "메리츠화재",
            "NH_YakMuN5ㄴ250120250101": "NH농협손해보험",
        }

    @classmethod
    def load_local(
        cls,
        folder_path: str,
        index_name: str = "faiss",
        index_extend: str = "index",
        metadata_is: bool = True,
    ) -> dict:
        if index_extend not in ["faiss", "index", "bin"]:
            raise ValueError("사용할 수 없는 파일 인덱스 확장자입니다.")

        path = Path(folder_path)
        index_path = str(path / f"{index_name}.{index_extend}")
        metadata_path = str(path / "metadata.json")
        index = faiss.read_index(index_path)

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"인덱스 파일을 찾을 수 없습니다: {index_path}")

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"메타데이터 파일을 찾을 수 없습니다: {metadata_path}")

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata_raw = json.load(f)

        if isinstance(metadata_raw, list):
            metadata = {}
            for i, item in enumerate(metadata_raw):
                metadata[str(i)] = item
        else:
            metadata = metadata_raw

        return index, metadata

    def load_collection(self, collection_name: str) -> bool:
        # 이미 로드된 컬렉션 확인
        for coll in self.collections:
            if coll["name"] == collection_name:
                print(f"{collection_name} 컬렉션이 이미 로드되어 있습니다.")
                return True

        # 하드코딩된 매핑 대신 동적으로 컬렉션 이름 사용
        # 예외 처리: 알려진 별칭이 있는 경우 실제 디렉토리 이름으로 매핑
        collection_mapping = {
            # DB손해보험 관련 매핑
            "db손해보험": "DBSonBo_YakMu20250123",
            "DB손해보험": "DBSonBo_YakMu20250123",
            "db손보": "DBSonBo_YakMu20250123",
            "디비손해보험": "DBSonBo_YakMu20250123",
            "디비손보": "DBSonBo_YakMu20250123",
            "디비": "DBSonBo_YakMu20250123",
            "DBSonbo_Yakwan20250123": "DBSonBo_YakMu20250123",
            # 삼성화재 관련 매핑
            "삼성화재": "Samsung_YakMu2404103NapHae20250113",
            "삼성": "Samsung_YakMu2404103NapHae20250113",
            "samsung": "Samsung_YakMu2404103NapHae20250113",
            # 하나손해보험 관련 매핑
            "하나손해보험": "HaNa_YakMuHaGaengPyo20250101",
            "하나손보": "HaNa_YakMuHaGaengPyo20250101",
            "하나": "HaNa_YakMuHaGaengPyo20250101",
            "hana": "HaNa_YakMuHaGaengPyo20250101",
            # 한화손해보험 관련 매핑
            "한화손해보험": "HanWha_YakHan20250201",
            "한화손보": "HanWha_YakHan20250201",
            "한화": "HanWha_YakHan20250201",
            "hanwha": "HanWha_YakHan20250201",
            # 흥국화재 관련 매핑
            "흥국화재": "Heung_YakMu250220250205",
            "흥국": "Heung_YakMu250220250205",
            "heung": "Heung_YakMu250220250205",
            # 현대해상 관련 매핑
            "현대해상": "HyunDai_YakMuSeH1Il2Nap20250213",
            "현대": "HyunDai_YakMuSeH1Il2Nap20250213",
            "hyundai": "HyunDai_YakMuSeH1Il2Nap20250213",
            # KB손해보험 관련 매핑
            "KB손해보험": "KB_YakKSeHaeMu250120250214",
            "KB손보": "KB_YakKSeHaeMu250120250214",
            "KB": "KB_YakKSeHaeMu250120250214",
            "케이비": "KB_YakKSeHaeMu250120250214",
            # 롯데손해보험 관련 매핑
            "롯데손해보험": "LotteSonBo_YakMuLDeo25011220250101",
            "롯데손보": "LotteSonBo_YakMuLDeo25011220250101",
            "롯데": "LotteSonBo_YakMuLDeo25011220250101",
            "lotte": "LotteSonBo_YakMuLDeo25011220250101",
            # MG손해보험 관련 매핑
            "MG손해보험": "MGSonBo_YakMuWon2404Se20250101",
            "MG손보": "MGSonBo_YakMuWon2404Se20250101",
            "MG": "MGSonBo_YakMuWon2404Se20250101",
            "엠지": "MGSonBo_YakMuWon2404Se20250101",
            # 메리츠화재 관련 매핑
            "메리츠화재": "Meritz_YakMu220250113",
            "메리츠": "Meritz_YakMu220250113",
            "meritz": "Meritz_YakMu220250113",
            # NH농협손해보험 관련 매핑
            "NH농협손해보험": "NH_YakMuN5250120250101",
            "NH손해보험": "NH_YakMuN5250120250101",
            "농협손해보험": "NH_YakMuN5250120250101",
            "NH손보": "NH_YakMuN5250120250101",
            "농협손보": "NH_YakMuN5250120250101",
            "NH": "NH_YakMuN5250120250101",
            "농협": "NH_YakMuN5250120250101",
        }

        # 로깅을 위해 원래 이름 저장
        original_name = collection_name

        # 매핑 적용
        actual_collection_name = collection_mapping.get(collection_name, collection_name)

        # 원본 이름과 매핑된 이름이 다른 경우 로그 출력
        if original_name != actual_collection_name:
            print(f"자동 변환: '{original_name}' -> '{actual_collection_name}'")

        collection_dir = os.path.join(self.base_path, actual_collection_name)

        # 만약 존재하지 않는 경로일 경우 추가 처리
        if not os.path.exists(collection_dir):
            for d in os.listdir(self.base_path):
                print(f"  - {d}")

            # sonbo/SONBO/Sonbo 대소문자 문제 처리
            if "sonbo" in actual_collection_name.lower() or "손보" in actual_collection_name:
                # 실제 존재하는 디렉토리 찾기
                for dir_name in os.listdir(self.base_path):
                    if "sonbo" in dir_name.lower() or "SonBo" in dir_name:
                        actual_collection_name = dir_name
                        print(f"DB손해보험 컬렉션 찾음: {dir_name}")
                        break
        index, metadata = CollectionLoader.load_local(
            folder_path=collection_dir,
            index_name="faiss",  # 보통 faiss.index 또는 index.faiss 중 하나
            index_extend="index",
        )

        # 메타데이터 개수 확인
        self.collections.append({"name": collection_name, "index": index, "metadata": metadata})

        return self.collections
