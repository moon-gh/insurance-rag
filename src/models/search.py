import faiss
import numpy as np

from config.settings import settings
from models.embeddings import UpstageEmbedding

upembedding = UpstageEmbedding(settings.upstage_api_key)


def search(query, collections, collection_names=None, top_k=2):
    if not collections:
        return [
            {
                "collection": "default",
                "id": "0",
                "score": 1.0,
                "metadata": {"text": "로드된 컬렉션이 없습니다."},
            }
        ]

    all_results = []
    use_collections = [c for c in collections if not collection_names or c["name"] in collection_names]
    if not use_collections:
        return [
            {
                "collection": "default",
                "id": "0",
                "score": 1.0,
                "metadata": {"text": "지정된 컬렉션을 찾을 수 없습니다."},
            }
        ]

    print("\n-------- 벡터 검색 시작 --------")
    print(f"쿼리: '{query}'")
    print(f"대상 컬렉션: {[c['name'] for c in use_collections]}")
    print(f"각 컬렉션당 top_k: {top_k}")

    query_embedding = upembedding.get_upstage_embedding(query)
    # 임베딩 형태 출력
    if isinstance(query_embedding, list):
        query_embedding = np.array(query_embedding, dtype=np.float32).reshape(1, -1)

    if len(query_embedding.shape) == 1:
        query_embedding = query_embedding.reshape(1, -1)  # 1D -> 2D

    query_dim = query_embedding.shape[1]

    # 각 컬렉션에서 항상 top_k개의 문서 검색
    for collection in use_collections:
        index = collection["index"]
        metadata = collection["metadata"]
        collection_name = collection["name"]

        print(f"\n검색 중: {collection_name} 컬렉션")

        if query_dim != index.d:
            print(f"차원 불일치: 쿼리={query_dim}, 인덱스={index.d}")
            # 차원이 다른 경우 벡터를 올바른 차원으로 패딩하거나 자름
            if query_dim < index.d:
                # 패딩: 부족한 차원을 0으로 채움
                padded = np.zeros((1, index.d), dtype=np.float32)
                padded[0, :query_dim] = query_embedding[0, :]
                query_embedding = padded
                print(f"쿼리 벡터를 {query_dim}에서 {index.d}로 패딩했습니다.")
            else:
                # 자름: 여분의 차원을 제거
                query_embedding = query_embedding[0, : index.d].reshape(1, -1)
                print(f"쿼리 벡터를 {query_dim}에서 {index.d}로 잘랐습니다.")

        # L2 정규화 다시 적용
        faiss.normalize_L2(query_embedding)

        # 검색 전 벡터 상태 로깅
        query_norm = np.linalg.norm(query_embedding)

        # 노름이 1과 크게 차이나면 경고
        if abs(query_norm - 1.0) > 1e-5:
            print(f"경고: 쿼리 벡터 노름이 1이 아닙니다: {query_norm}")
            # 강제로 정규화
            query_embedding = query_embedding / query_norm
            print(f"강제 정규화 후 노름: {np.linalg.norm(query_embedding)}")

        # 각 컬렉션에서 항상 top_k개의 문서 검색
        distances, indices = index.search(query_embedding, top_k)

        # 내적 값이 1보다 크면 경고
        if np.any(distances > 1.01):  # 약간의 오차 허용
            print(f"경고: 내적 값이 1보다 큽니다. 최댓값: {np.max(distances)}")
            # 내적 값이 1을 초과하는 경우 1로 제한
            distances = np.minimum(distances, 1.0)

        # 내적 기반 검색에서는 값이 클수록 유사도가 높음
        print(f"검색 결과: 내적 값={distances}, 인덱스={indices}")

        # 유사도 점수 변환 (내적 값은 -1~1 범위, 높을수록 유사)
        # 결과를 0~1 범위로 정규화 (옵션)
        normalized_scores = (distances + 1) / 2

        collection_results = []
        for i, (idx, score) in enumerate(zip(indices[0], normalized_scores[0])):
            if idx != -1:  # -1은 결과가 없음을 의미
                # 메타데이터에서 해당 인덱스의 정보 가져오기
                doc_id = str(idx)

                # 디버깅: 메타데이터 키 확인
                print(f"메타데이터 키 검색: {doc_id}")

                # 메타데이터 키가 존재하는지 확인
                if doc_id in metadata:
                    print(f"메타데이터에서 키 {doc_id} 찾음")
                    doc_metadata = metadata[doc_id]
                    # 결과 추가 (점수는 높을수록 유사함을 의미)
                    collection_results.append(
                        {
                            "collection": collection_name,
                            "id": doc_id,
                            "score": float(score),  # 0~1 사이 값, 높을수록 유사
                            "metadata": doc_metadata,
                        }
                    )
                else:
                    # 키가 존재하지 않으면 다른 형식으로 시도
                    print(f"메타데이터에서 키 {doc_id} 찾을 수 없음. 다른 형식 시도...")

                    # 정수 키로 시도
                    int_id = str(int(idx))
                    if int_id in metadata:
                        print(f"정수 키 {int_id}로 찾음")
                        doc_metadata = metadata[int_id]
                        collection_results.append(
                            {
                                "collection": collection_name,
                                "id": int_id,
                                "score": float(score),
                                "metadata": doc_metadata,
                            }
                        )
                    else:
                        # 인덱스가 리스트의 범위 내에 있는지 확인
                        try:
                            # 메타데이터가 실제로는 리스트이거나 인덱스 기반인 경우
                            idx_int = int(idx)
                            meta_len = len(metadata)
                            if 0 <= idx_int < meta_len:
                                print(f"인덱스 {idx_int}를 배열 접근으로 시도 (배열 길이: {meta_len})")
                                try:
                                    # 리스트로 변환된 딕셔너리에서 키로 접근
                                    list_keys = list(metadata.keys())
                                    if idx_int < len(list_keys):
                                        key = list_keys[idx_int]
                                        doc_metadata = metadata[key]
                                        print(f"변환된 키 {key}로 찾음")
                                        collection_results.append(
                                            {
                                                "collection": collection_name,
                                                "id": key,
                                                "score": float(score),
                                                "metadata": doc_metadata,
                                            }
                                        )
                                        continue
                                except Exception as e:
                                    print(f"키 변환 접근 오류: {e}")
                        except Exception as e:
                            print(f"인덱스 기반 접근 시도 중 오류: {e}")

                        # 메타데이터 키 출력 (처음 10개만)
                        meta_keys = list(metadata.keys())[:10]
                        print(f"메타데이터 샘플 키: {meta_keys}")

                        # 모든 방법 실패 시 기본 메타데이터 생성
                        print("모든 키 검색 실패, 기본 메타데이터 사용")
                        collection_results.append(
                            {
                                "collection": collection_name,
                                "id": doc_id,
                                "score": float(score),
                                "metadata": {"text": f"인덱스 {idx}의 메타데이터를 찾을 수 없습니다."},
                            }
                        )
                        # 이 결과도 all_results에 추가
                        all_results.append(
                            {
                                "collection": collection_name,
                                "id": doc_id,
                                "score": float(score),
                                "metadata": {"text": f"인덱스 {idx}의 메타데이터를 찾을 수 없습니다."},
                            }
                        )

        # all_results에 collection_results 추가
        all_results.extend(collection_results)

        print(f"{collection_name} 컬렉션에서 {len(collection_results)}개 결과 찾음")
        # 각 청크의 시작 부분 미리보기 출력
        for i, result in enumerate(collection_results):
            text = result.get("metadata", {}).get("text", "")
            preview = text[:100] + "..." if text else "텍스트 없음"
            print(f"  청크 {i+1}: 점수={result['score']:.4f}, 미리보기: {preview}")

    # 결과를 점수에 따라 정렬
    all_results.sort(key=lambda x: x["score"])

    print(f"\n총 {len(all_results)}개 청크 검색됨")
    print("-------- 벡터 검색 완료 --------\n")

    # 트레이싱 메타데이터 업데이트
    return (
        all_results
        if all_results
        else [
            {
                "collection": "default",
                "id": "0",
                "score": 1.0,
                "metadata": {"text": "검색 결과를 찾을 수 없습니다."},
            }
        ]
    )
