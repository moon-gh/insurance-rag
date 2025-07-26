import os

import numpy as np
from langchain_upstage import UpstageEmbeddings


class UpstageEmbedding:
    def __init__(self, upstage_api_key=None):
        self.api_key = upstage_api_key or os.getenv("UPSTAGE_API_KEY")
        if not self.api_key or len(self.api_key) < 10:
            raise ValueError(f"유효한 Upstage API 키가 없습니다. 현재 키: {self.api_key}")
        self.cached_embeddings = {}
        self.upstage = UpstageEmbeddings(
            api_key=self.api_key,
            model="solar-embedding-1-large",
        )

    def get_upstage_embedding(self, text: str) -> float:
        if text in self.cached_embeddings:
            return self.cached_embeddings[text]

        # 텍스트 임베딩 생성
        embedding = self.upstage.embed_query(text)

        # 벡터 변환 및 정규화
        vector = np.array(embedding, dtype=np.float32).reshape(1, -1)

        # 결과 캐시
        self.cached_embeddings[text] = vector
        return vector
