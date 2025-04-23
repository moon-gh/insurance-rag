# RAG (Retrieval-Augmented Generation) for 보험 챗봇

이 프로젝트는 보험 관련 질의응답 시스템을 위한 RAG(Retrieval-Augmented Generation) 구현입니다.   
보험 약관과 비교설계 데이터를 활용하여 사용자 질문에 정확한 답변을 제공합니다.

## 주요 기능

- 보험 약관에 대한 질의응답
- 보험사별 비교설계 정보 제공
- 질의 의도분류 (보험 약관/비교설계/일반채팅)

## 프로젝트 구조

```
rag/
├── poc/                            # 초기 코드
├── src/                            # 소스 코드
│   └── config                      # 설정 폴더
│       └── settings.py             # 설정 파일
│   └── db                          # DB 폴더
│       ├── schema.py               # 스키마 파일
│       └── sql_utils.py            # sql 유틸리티 파일
│   └── models                      # 모델 폴더
│       ├── collection_loader.py    # 콜렉션 로더 파일
│       ├── generate_answer.py      # 답변 생성 파일
│       ├── search.py               # 검색 파일
│       └── embeddings.py           # 임베딩 파일
│   └── modules                     # 모듈 폴더
│       ├── compare.py              # 비교약관 모듈
│       ├── intent.py               # 의도분류 모듈
│       └── policy.py               # 정책질의 모듈
│   └── options                     # 유틸리티 함수
│       └── enums.py
│   └── prompts                     # 프롬프트 폴더
│       ├── base_prompt.jinja2
│       ├── example_prompt.jinja2
│       └── intent_prompt.jinja2
│   ├── tests                       # 테스트 폴더
│   └── util                        # 유틸리티 폴더
│       └── utils.py                # 유틸리티 파일
│   ├── main.py                     # 메인 실행 파일
├── insu_data/                      # 벡터 DB 저장소
│   ├── Samsung_YakMu2404103NapHae20250113/
│   ├── DBSonBo_YakMu20250123/
│   └── ...
├── .gitignore                      
├── README.md
└── requirements.txt
```

## 환경 설정

필요한 패키지를 설치하려면:

```bash
pip install -r requirements.txt
```

다음 환경 변수를 설정해야 합니다:
- `OPENAI_API_KEY`: OpenAI API 키
- `UPSTAGE_API_KEY`: Upstage API 키

## 실행 방법

RAG 모듈을 직접 실행하려면:

```bash
cd /path/rag
python src/main.py
```
