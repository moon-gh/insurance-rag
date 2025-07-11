import numpy as np
import pytest
from numpy.typing import NDArray

from models.search import FaissSearch


class DummyIndex:
    def __init__(self, d: int, distances: NDArray[np.float32], indices: NDArray[np.int64]):
        self.d = d
        self._distances = np.array(distances, dtype=np.float32)
        self._indices = np.array(indices, dtype=np.int64)

    def search(self, query: str, top_k: int) -> tuple[NDArray[np.float32], NDArray[np.int64]]:
        return self._distances.reshape(1, -1), self._indices.reshape(1, -1)


@pytest.mark.parametrize(
    "query_dim, index_dim, expected_shape",
    [
        (4096, 4096, (1, 4096)),
        (2048, 4096, (1, 4096)),
        (4096, 3072, (1, 3072)),
    ],
)
def test_pad_embedding_shape(query_dim: int, index_dim: int, expected_shape: tuple[int, int]) -> None:
    search_results = FaissSearch(query="현대해상의 기본플랜 보험료를 알려줘", total_collections=[])
    query_embedding = np.arange(query_dim, dtype=np.float32).reshape(1, -1)
    padded = search_results.pad_embedding(
        query_embedding,
        DummyIndex(
            d=index_dim,
            distances=[0.0],
            indices=[0],
        ),
        query_dim,
    )
    assert padded.shape == expected_shape
    if query_dim < index_dim:
        assert np.all(padded[0, :query_dim] == query_embedding[0])
    elif query_dim > index_dim:
        assert np.all(padded[0] == query_embedding[0, :index_dim])
    else:
        assert np.all(padded == query_embedding)


def test_search_L2_index_by_query_and_clipping() -> None:
    dummy = DummyIndex(d=3, distances=[1.5, 0.8], indices=[2, 3])
    search_results = FaissSearch(query="현대해상의 기본플랜 보험료를 알려줘", total_collections=[], collection_names=[])
    emb = np.array([[2.0, 0.0, 0.0]], dtype=np.float32)
    distance, indices = search_results.search_L2_index_by_query(dummy, emb)
    assert np.all(distance <= 1.0)
    assert distance.shape == (2,)
    assert indices.shape == (2,)


def test_get_results_returns_default_when_no_collections() -> None:
    search_results = FaissSearch(query="현대해상의 기본플랜 보험료를 알려줘", total_collections=[])
    results = search_results.get_results()
    assert results == [
        {
            "collection": "default",
            "id": "0",
            "score": 1.0,
            "metadata": {"text": "로드된 컬렉션이 없습니다."},
        }
    ]
