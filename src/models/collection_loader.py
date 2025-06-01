import json
import os
from pathlib import Path
from typing import Any

import faiss
from langchain.embeddings.base import Embeddings

from options.insu_name import insu_match


class CollectionLoader:
    def __init__(self, vector_path: str, embeddings: Embeddings):
        self.base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), vector_path)
        self.embeddings = embeddings
        self.collections: list[dict[str, Any]] = []

    @classmethod
    def load_local(
        cls,
        folder_path: str,
        index_name: str = "faiss",
        index_extend: str = "index",
    ) -> tuple[faiss.Index, dict[str, Any]]:
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

    def load_collection(self, collection_name: str) -> list[dict[str, Any]]:
        # 이미 로드된 컬렉션 확인
        for coll in self.collections:
            if coll["name"] == collection_name:
                print(f"{collection_name} 컬렉션이 이미 로드되어 있습니다.")

        if collection_name not in insu_match.values():
            raise ValueError(f"{collection_name} 컬렉션을 찾을 수 없습니다.")

        collection_dir = os.path.join(self.base_path, collection_name)

        index, metadata = CollectionLoader.load_local(
            folder_path=collection_dir,
            index_name="faiss",  # 보통 faiss.index 또는 index.faiss 중 하나
            index_extend="index",
        )

        self.collections.append({"name": collection_name, "index": index, "metadata": metadata})
        return self.collections
