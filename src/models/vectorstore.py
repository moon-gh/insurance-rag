import faiss
import json
import os
from pathlib import Path
from langchain.embeddings.base import Embeddings


def load_local(
    folder_path: str,
    index_name: str = "faiss",
    index_extend: str = "index",
    metadata_is: bool = True,
) -> dict:
    if index_extend not in ["faiss", "index", "bin"]:
        raise ValueError("사용할 수 없는 파일 인덱스 확장자입니다.")

    path = Path(folder_path)
    index_path = str(path / f"{index_name}.{index_extend}")
    metadata_path = str(path / f"metadata.json")
    index = faiss.read_index(index_path)

    if not os.path.exists(index_path):
        raise FileNotFoundError(f"인덱스 파일을 찾을 수 없습니다: {index_path}")

    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"메타데이터 파일을 찾을 수 없습니다: {metadata_path}")

    index_type = type(index).__name__
    print(f"로드된 인덱스 타입: {index_type}")
    print(f"인덱스 차원: {index.d}, 벡터 수: {index.ntotal}")

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata_raw = json.load(f)

    if isinstance(metadata_raw, list):
        print(f"메타데이터가 리스트 형식입니다. 딕셔너리로 변환합니다.")
        metadata = {}
        for i, item in enumerate(metadata_raw):
            metadata[str(i)] = item
        print(f"리스트를 딕셔너리로 변환 완료: {len(metadata)}개 항목")
    else:
        metadata = metadata_raw

    # 메타데이터 형식 분석
    metadata_count = len(metadata)
    sample_keys = list(metadata.keys())[:5]
    print(f"메타데이터 항목 수: {metadata_count}")
    print(f"메타데이터 샘플 키: {sample_keys}")
    if sample_keys:
        key_types = [type(k) for k in sample_keys]
        print(f"메타데이터 키 타입: {key_types}")

        # 첫 번째 메타데이터 항목 내용 확인
        first_item = metadata[sample_keys[0]]
        print(
            f"메타데이터 첫 항목: {first_item.keys() if isinstance(first_item, dict) else 'Not a dict'}"
        )

    return index, metadata


def search(query: str, collection_name=None, top_k=2):
    return
