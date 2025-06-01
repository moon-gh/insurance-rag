# An Agent Insurance Chatbot to assist GA agent.

이 프로젝트는 보험 관련 질의응답 시스템을 위한 Hybrid RAG(Retrieval-Augmented Generation)챗봇입니다.
보험 약관 질의 모듈과 비교설계 모듈을 활용하여 사용자 질문에 정확한 답변을 제공합니다.
- 보험약관질의 모듈은 11개의 보험사 보험약관 중 상위 2개씩을 가져와 11개의 collection을 만들어 FAISS VectorDB적재 후 검색
- 비교설계 모듈은 11개 보험사의 보험상품의 보험료를 DB적재 및 질문에 대한 답변을 SQL쿼리로 생성해 json구조로 변환한 뒤 그래프로 도식화하며 쉽게 보험사별 보험상품 가격을 비교분석할 수 있도록 도와줌

## Main Features

- 보험 약관에 대한 질의응답
- 보험사별 보험상품 비교설계 질의응답 및 그래프 도식화
- 질의 의도분류 (보험 약관/비교설계/일반채팅)

## 프로젝트 구조

```
rag/
├── poc/                            # 초기 레거시 코드
├── src/                            # 소스 코드
│   ├── config/                     # 설정 폴더
│   │   └── settings.py
│   ├── db/                         # DB 폴더
│   │   ├── schema.py
│   │   └── sql_utils.py
│   ├── models/
│   │   ├── collection_loader.py    # 콜렉션 로더 파일
│   │   ├── generate_answer.py      # 답변 생성 파일
│   │   ├── search.py               # 검색 파일
│   │   └── embeddings.py           # 임베딩 파일
│   ├── modules/
│   │   └── handler.py              # 보험약관질의 모듈
│   ├── options/
│   │   └── enums.py
│   ├── prompts/                    # 프롬프트 폴더
│   │   ├── base_prompt.jinja2
│   │   ├── example_prompt.jinja2
│   │   └── intent_prompt.jinja2
│   ├── tests/                      # 테스트 폴더
│   ├── util/                       # 유틸리티 폴더
│   │   └── utils.py                # 유틸리티 파일
│   ├── insu_data/                  # 벡터 DB 저장소
│   │   ├── Samsung_YakMu2404103NapHae20250113/
│   │   ├── DBSonBo_YakMu20250123/
│   │   └── ...
│   └── main.py
├── .gitignore
├── README.md
└── requirements.txt
```

## Prerequisites

- Python 3.11+
- 11개 보험사 보험약관 VectorDatabase 데이터 준비
- 11개 보험사 비교설계 4개 Table 준비

## Installation
**1. Clone the repository**
```bash
git clone https://github.com/sessac-multi-docu/rag.git
cd rag
```
**2. Create a virtual environment**
```bash
brew install pyenv # (macOS)
pyenv install 3.11.3
pyenv virtualenv 3.11.3 insupanda
pyenv activate insupanda
```
**3. Install dependencies**
```bash
pip install -r requirements.txt
```

## Settings
다음 환경 변수를 설정해야 합니다:
- `OPENAI_API_KEY`: OpenAI API 키
- `UPSTAGE_API_KEY`: Upstage API 키

보험비교설계 데이터가 담긴 데이터베이스 환경설정
- `db_password`: <데이터베이스 비밀번호>
- `db_host`: <데이터베이스 호스트>
- `db_port`: <데이터베이스 포트>
- `db_user`: <데이터베이스 사용자명>
- `db_database`: <데이터베이스 비밀번호>

## How to Run

RAG 모듈을 직접 실행하려면:

```bash
cd /rag
python src/main.py
```

## Code Quality
pre-commit (black, isort, flake8, mypy)으로 code quality 유지
```bash
pre-commit autoupdate # Automatically update to the latest packages.
pre-commit install
pre-commit run --all-files # check your code quality.
```
## CI (Continuous Integration) Pipeline
Github Action의 super-liner로 구동. 모든 push와 main branch에 대한 PR(Pull Request)마다 검사를 자동적으로 실행
- black (Checking format)
- flake8 (Linting)
- isort (Sorting import)
- mypy (Checking type hint)
