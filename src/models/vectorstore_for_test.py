import os
import json
import faiss
import operator
import numpy as np
from pathlib import Path
from typing import (
    Any,
    Callable,
    Optional,
    Union,
)
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.utils import (
    DistanceStrategy,
    maximal_marginal_relevance,
)

index = faiss.IndexFlatL2(len(OpenAIEmbeddings().embed_query("hello world")))
embedding_function = OpenAIEmbeddings()
index_to_docstore_id = {}
docstore = InMemoryDocstore()
distance_strategy = DistanceStrategy.EUCLIDEAN_DISTANCE
normalize_L2 = False
# https://api.python.langchain.com/en/latest/vectorstores/langchain_community.vectorstores.faiss.FAISS.html

vector_store = FAISS(
    embedding_function=OpenAIEmbeddings(),
    index=index,
    docstore=InMemoryDocstore(),
    index_to_docstore_id={},
)

# Document 추가
from langchain_core.documents import Document

document_1 = Document(
    page_content="foo",
    metadata={"baz": "bar"},
)
document_2 = Document(page_content="thud", metadata={"bar": "baz"})
document_3 = Document(page_content="i will be deleted :(")

documents = [document_1, document_2, document_3]
ids = ["1", "2", "3"]
abc = vector_store.add_documents(documents=documents, ids=ids)


def add_documents(self, documents: list[Document], **kwargs: Any) -> list[str]:
    """Add or update documents in the vectorstore.

    Args:
        documents: Documents to add to the vectorstore.
        kwargs: Additional keyword arguments.
            if kwargs contains ids and documents contain ids,
            the ids in the kwargs will receive precedence.

    Returns:
        List of IDs of the added texts.

    Raises:
        ValueError: If the number of ids does not match the number of documents.
    """
    if type(self).add_texts != VectorStore.add_texts:
        if "ids" not in kwargs:
            ids = [doc.id for doc in documents]

            # If there's at least one valid ID, we'll assume that IDs
            # should be used.
            if any(ids):
                kwargs["ids"] = ids

        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        return self.add_texts(texts, metadatas, **kwargs)
    msg = (
        f"`add_documents` and `add_texts` has not been implemented "
        f"for {self.__class__.__name__} "
    )
    raise NotImplementedError(msg)


def similarity_search(
    query: str,
    k: int = 4,
    filter: Optional[Union[Callable, dict[str, Any]]] = None,
    fetch_k: int = 20,
    **kwargs: Any,
) -> list[Document]:
    """Return docs most similar to query.

    Args:
        query: Text to look up documents similar to.
        k: Number of Documents to return. Defaults to 4.
        filter: (Optional[Dict[str, str]]): Filter by metadata. Defaults to None.
        fetch_k: (Optional[int]) Number of Documents to fetch before filtering.
                  Defaults to 20.

    Returns:
        List of Documents most similar to the query.
    """
    docs_and_scores = similarity_search_with_score(
        query, k, filter=filter, fetch_k=fetch_k, **kwargs
    )
    print("kkkk", docs_and_scores)
    return [doc for doc, _ in docs_and_scores]


def similarity_search_with_score(
    query: str,
    k: int = 4,
    filter: Optional[Union[Callable, dict[str, Any]]] = None,
    fetch_k: int = 20,
    **kwargs: Any,
) -> list[tuple[Document, float]]:
    """Return docs most similar to query.

    Args:
        query: Text to look up documents similar to.
        k: Number of Documents to return. Defaults to 4.
        filter (Optional[Dict[str, str]]): Filter by metadata.
            Defaults to None. If a callable, it must take as input the
            metadata dict of Document and return a bool.

        fetch_k: (Optional[int]) Number of Documents to fetch before filtering.
                  Defaults to 20.

    Returns:
        List of documents most similar to the query text with
        L2 distance in float. Lower score represents more similarity.
    """
    embedding = embedding_function.embed_query(query)
    docs = similarity_search_with_score_by_vector(
        embedding,
        k,
        filter=filter,
        fetch_k=fetch_k,
        **kwargs,
    )
    return docs


def dependable_faiss_import(no_avx2: Optional[bool] = None) -> Any:
    """
    Import faiss if available, otherwise raise error.
    If FAISS_NO_AVX2 environment variable is set, it will be considered
    to load FAISS with no AVX2 optimization.

    Args:
        no_avx2: Load FAISS strictly with no AVX2 optimization
            so that the vectorstore is portable and compatible with other devices.
    """
    if no_avx2 is None and "FAISS_NO_AVX2" in os.environ:
        no_avx2 = bool(os.getenv("FAISS_NO_AVX2"))

    try:
        if no_avx2:
            from faiss import swigfaiss as faiss
        else:
            import faiss
    except ImportError:
        raise ImportError(
            "Could not import faiss python package. "
            "Please install it with `pip install faiss-gpu` (for CUDA supported GPU) "
            "or `pip install faiss-cpu` (depending on Python version)."
        )
    return faiss


def similarity_search_with_score_by_vector(
    embedding: list[float],
    k: int = 4,
    filter: Optional[Union[Callable, dict[str, Any]]] = None,
    fetch_k: int = 20,
    **kwargs: Any,
) -> list[tuple[Document, float]]:
    """Return docs most similar to query.

    Args:
        embedding: Embedding vector to look up documents similar to.
        k: Number of Documents to return. Defaults to 4.
        filter (Optional[Union[Callable, Dict[str, Any]]]): Filter by metadata.
            Defaults to None. If a callable, it must take as input the
            metadata dict of Document and return a bool.
        fetch_k: (Optional[int]) Number of Documents to fetch before filtering.
                  Defaults to 20.
        **kwargs: kwargs to be passed to similarity search. Can include:
            score_threshold: Optional, a floating point value between 0 to 1 to
                filter the resulting set of retrieved docs

    Returns:
        List of documents most similar to the query text and L2 distance
        in float for each. Lower score represents more similarity.
    """

    faiss = dependable_faiss_import()
    vector = np.array([embedding], dtype=np.float32)
    if normalize_L2:
        faiss.normalize_L2(vector)
    scores, indices = index.search(vector, k if filter is None else fetch_k)
    docs = []

    # if filter is not None:
    #     filter_func = _create_filter_func(filter)

    for j, i in enumerate(indices[0]):
        if i == -1:
            # This happens when not enough docs are returned.
            continue
        print(i, index_to_docstore_id)
        _id = index_to_docstore_id[i]
        doc = docstore.search(_id)
        if not isinstance(doc, Document):
            raise ValueError(f"Could not find document for id {_id}, got {doc}")
        if filter is not None:
            pass
            # if filter_func(doc.metadata):
            #     docs.append((doc, scores[0][j]))
        else:
            docs.append((doc, scores[0][j]))

    score_threshold = kwargs.get("score_threshold")
    if score_threshold is not None:
        cmp = (
            operator.ge
            if distance_strategy
            in (DistanceStrategy.MAX_INNER_PRODUCT, DistanceStrategy.JACCARD)
            else operator.le
        )
        docs = [
            (doc, similarity)
            for doc, similarity in docs
            if cmp(similarity, score_threshold)
        ]
    return docs[:k]


# Search
results = vector_store.similarity_search(query="thud", k=1)
# results = similarity_search(query="thud", k=1)
for doc in results:
    print(f"* {doc.page_content} [{doc.metadata}]")


# # Search with filter
# results = vector_store.similarity_search(query="thud", k=1, filter={"bar": "baz"})
# for doc in results:
#     print(f"* {doc.page_content} [{doc.metadata}]")

# # Serach with score
# results = vector_store.similarity_search_with_score(query="qux", k=1)
# for doc, score in results:
#     print(f"* [SIM={score:3f}] {doc.page_content} [{doc.metadata}]")

# # Use as Retriever
# retriever = vector_store.as_retriever(
#     search_type="mmr",
#     search_kwargs={"k": 1, "fetch_k": 2, "lambda_mult": 0.5},
# )
# retriever.invoke("thud")
