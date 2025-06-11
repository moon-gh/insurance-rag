import logging

import faiss
import numpy as np
from numpy.typing import NDArray

from config.settings import settings
from models.dict_types import DocId, DocIDMetadata, OrganizedCollection, RawCollection
from models.embeddings import UpstageEmbedding

InsuFileNames = str
upembedding = UpstageEmbedding(settings.upstage_api_key)


class FaissSearch:
    def __init__(
        self,
        query: str,
        total_collections: list[RawCollection],
        collection_names: list[InsuFileNames] = [],
        top_k: int = 2,
    ):
        self.query = query
        self.default_document = {
            "collection": "default",
            "id": "0",
            "score": 1.0,
            "metadata": {"text": "로드된 컬렉션이 없습니다."},
        }
        self.collections = total_collections
        self.target_collections = [
            collection
            for collection in total_collections
            if not collection_names or collection["name"] in collection_names
        ]
        self.logger = logging.getLogger(self.__class__.__name__)
        self.top_k = top_k

    def pad_embedding(
        self, query_embedding: NDArray[np.float32], index: faiss.Index, query_dim: int
    ) -> NDArray[np.float32]:
        index_dim = index.d

        if query_dim == index_dim:
            return query_embedding

        if query_dim < index_dim:
            padded_embedding = np.zeros((1, index_dim), dtype=query_embedding.dtype)
            padded_embedding[0, :query_dim] = query_embedding[0, :]
            return padded_embedding

        trimmed_embedding = query_embedding[0, :index_dim]
        return trimmed_embedding

    def search_L2_index_by_query(
        self, index: faiss.Index, query_embedding: NDArray[np.float32]
    ) -> tuple[NDArray[np.float32], NDArray[np.int64]]:
        faiss.normalize_L2(query_embedding)

        distance, indices = index.search(query_embedding, self.top_k)
        distance = np.minimum(distance, 1.0)
        return distance[0], indices[0]

    def search_metadata_by_index(
        self,
        distances: NDArray[np.float32],
        indices: NDArray[np.int64],
        metadata: dict[DocId, DocIDMetadata],
        collection_filename: str,
    ) -> list[OrganizedCollection]:
        self.logger.info(f"검색 중: {collection_filename} 컬렉션")
        collection_results: list[OrganizedCollection] = []
        for index, dist in zip(indices, distances):
            doc_id = str(index)

            if doc_id not in metadata or index == -1:
                logging.warning(f"메타데이터에서 키 {doc_id} 찾을 수 없습니다.")
                collection_results.append(self.default_document)
                continue

            doc_metadata = metadata[doc_id]
            collection_results.append(
                {
                    "collection": collection_filename,
                    "doc_id": doc_id,
                    "score": float(dist),
                    "metadata": doc_metadata,
                }
            )
        return collection_results

    def get_results(self) -> list[dict[DocId, DocIDMetadata]]:
        self.logger.info("-------- 벡터 검색 시작 --------")
        self.logger.info(f"쿼리: '{self.query}'")
        self.logger.info(f"대상 컬렉션: {[collection['name'] for collection in self.target_collections]}")
        self.logger.info(f"각 컬렉션당 top_k: {self.top_k}")

        if not self.collections or not self.target_collections:
            return [self.default_document]

        total_collection_result: list[dict[DocId, DocIDMetadata]] = []
        query_embedding = upembedding.get_upstage_embedding(self.query)
        query_dim = query_embedding.shape[1]
        for collection in self.target_collections:
            index = collection["index"]
            metadata = collection["metadata"]
            collection_name = collection["name"]
            query_embedding = self.pad_embedding(query_embedding, index, query_dim)
            score, indices = self.search_L2_index_by_query(index, query_embedding)
            collection_results = self.search_metadata_by_index(score, indices, metadata, collection_name)
            total_collection_result.extend(collection_results)
        self.logger.info(f"총 {len(total_collection_result)}개 청크 검색됨")
        self.logger.info("-------- 벡터 검색 완료 --------")
        return total_collection_result if total_collection_result else [self.default_document]
