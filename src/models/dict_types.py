from typing import Optional, TypedDict

import faiss

InsuFileName = str
DocId = str


class DocIDMetadata(TypedDict):
    header1: Optional[str]
    source: Optional[str]
    text: str


class RawCollection(TypedDict):
    name: InsuFileName
    index: faiss.Index
    metadata: dict[DocId, DocIDMetadata]


class OrganizedCollection(TypedDict):
    collection: InsuFileName
    doc_id: DocId
    score: float
    metadata: DocIDMetadata
