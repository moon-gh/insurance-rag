import os
from dotenv import load_dotenv
import mysql.connector
import openai
from typing import Optional
import re
import json
from datetime import datetime

# 환경 설정
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# 데이터베이스 연결 설정
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1234",
    "database": "insu"
}

# DB 스키마 정의
DB_SCHEMA = """-- 1. 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS insu DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE insu; 

-- 2. 보험 비교 설계 테이블 (comparison)
CREATE TABLE comparison (
    custom_name VARCHAR(255) NOT NULL COMMENT '성명',
    insu_age TINYINT UNSIGNED NOT NULL COMMENT '보험나이',
    sex TINYINT(1) NOT NULL COMMENT '성별 (0: 여자, 1: 남자)',
    product_type VARCHAR(50) NOT NULL COMMENT '상품유형',
    expiry_year VARCHAR(10) NOT NULL COMMENT '만기',
    company_id VARCHAR(20) NOT NULL COMMENT '보험사ID',
    product_id VARCHAR(20) NOT NULL COMMENT '보험ID',
    coverage_id VARCHAR(20) NOT NULL COMMENT '보장항목ID',
    premium_amount INT NOT NULL COMMENT '보험료',
    PRIMARY KEY (insu_age, sex, product_type, company_id, product_id, coverage_id)
);

-- 3. 보장항목 테이블 (coverage)
CREATE TABLE coverage (
    coverage_id VARCHAR(20) NOT NULL COMMENT '보장항목ID',
    coverage_name VARCHAR(255) NOT NULL COMMENT '보장항목명',
    default_coverage_amount DECIMAL(15,2) NOT NULL COMMENT '초기세팅 보험금',
    is_default TINYINT(1) NOT NULL COMMENT '1: default, 0: not default',
    PRIMARY KEY (coverage_id)
);

-- 4. 보험사 테이블 (insu_company)
CREATE TABLE insu_company (
    company_id VARCHAR(20) NOT NULL COMMENT '보험사ID',
    company_name VARCHAR(255) NOT NULL COMMENT '보험사명',
    is_default TINYINT(1) NOT NULL COMMENT '1: default, 0: not default',
    PRIMARY KEY (company_id)
);

-- 5. 보험상품 테이블 (insu_product)
CREATE TABLE insu_product (
    company_id VARCHAR(20) NOT NULL COMMENT '보험사ID',
    product_id VARCHAR(20) NOT NULL COMMENT '보험ID',
    product_name VARCHAR(255) NOT NULL COMMENT '보험명',
    is_default TINYINT(1) NOT NULL COMMENT '1: default, 0: not default',
    PRIMARY KEY (company_id, product_id),
    FOREIGN KEY (company_id) REFERENCES insu_company(company_id) ON DELETE CASCADE
);"""

# 기본 프롬프트 설정
BASE_PROMPT = """당신은 보험 데이터베이스 SQL 전문가입니다.
보험료를 알려달라고 하면 다음 규칙을 따라 SQL 쿼리를 작성하세요:

[필수 포함 조건]
모든 SQL 쿼리의 WHERE 절에는 반드시 다음 4가지 조건이 포함되어야 합니다:
1. c.insu_age = {age}
2. c.sex = {sex_num}
3. c.product_type = '{product_type}'
4. c.expiry_year = '{expiry_year}'

[필수 테이블 조인]
1. 보험사 정보는 반드시 포함되어야 합니다:
   - JOIN insu_company ic ON c.company_id = ic.company_id
2. 보험상품 정보도 반드시 포함되어야 합니다:
   - JOIN insu_product ip ON c.company_id = ip.company_id AND c.product_id = ip.product_id
3. 보장항목 정보도 반드시 포함되어야 합니다:
   - JOIN coverage cv ON c.coverage_id = cv.coverage_id

[쿼리 작성 규칙]
1. 보험료 합계를 조회할 때는 다음 형식을 사용하세요:
SELECT 
    ic.company_name AS 보험사명,
    ip.product_name AS 상품명,
    ROUND(SUM(c.premium_amount)) AS 보험료합계
FROM comparison c
JOIN insu_company ic ON c.company_id = ic.company_id
JOIN insu_product ip ON c.company_id = ip.company_id AND c.product_id = ip.product_id
JOIN coverage cv ON c.coverage_id = cv.coverage_id
WHERE [필수 조건들]
GROUP BY ic.company_name, ip.product_name
ORDER BY ic.company_name, ip.product_name;

2. "보장항목별" 또는 "상세" 단어가 포함된 경우 반드시 다음 WITH 구문을 사용해야 합니다:
WITH company_totals AS (
    SELECT 
        ic.company_name AS 보험사명,
        ROUND(SUM(c.premium_amount)) AS 보험료합계
    FROM comparison c
    JOIN insu_company ic ON c.company_id = ic.company_id
    WHERE [필수 조건들]
    GROUP BY ic.company_name
),
detailed_coverage AS (
    SELECT DISTINCT
        ic.company_name AS 보험사명,
        ip.product_name AS 상품명,
        cv.coverage_name AS 보장항목명,
        c.premium_amount AS 보험료,
        cv.coverage_id AS sort_id
    FROM comparison c
    JOIN insu_company ic ON c.company_id = ic.company_id
    JOIN insu_product ip ON c.company_id = ip.company_id AND c.product_id = ip.product_id
    JOIN coverage cv ON c.coverage_id = cv.coverage_id
    WHERE [필수 조건들]
)
SELECT * FROM (
    SELECT '합계' AS 구분, ct.보험사명, NULL AS 상품명, NULL AS 보장항목명, ct.보험료합계 AS 보험료, '0' AS sort_id
    FROM company_totals ct
    UNION ALL
    SELECT '상세' AS 구분, dc.보험사명, dc.상품명, dc.보장항목명, dc.보험료, dc.sort_id
    FROM detailed_coverage dc
) result
ORDER BY 보험사명, 구분 DESC, 상품명, sort_id;

[추가 규칙]
1. 명시된 조건을 제외한 company_id, product_id 등에는 특별한 조건을 걸지 않습니다
2. 결과는 첫째자리에서 반올림하여 소수점 없이 표시합니다
3. SQL 쿼리만 출력하고 설명이나 주석을 추가하지 마세요
4. product_type은 'nr' 또는 'r' 값만 사용하세요
5. 마크다운 형식(```sql)을 사용하지 말고 순수한 SQL 쿼리문만 반환하세요
6. 정확한 데이터 매칭을 위한 규칙:
   - 회사명이나 보장명을 조회할 때는 LIKE 연산자를 사용하세요
   - 회사명: LIKE '%삼성%'
   - 보장명: LIKE '%유사암%' 또는 LIKE '%진단비%'
7. '기본플랜'은 coverage table의 is_default = '1'인 경우입니다
8. 연령 범위 조회 시에는 BETWEEN을 사용하세요

현재 조건: 
- 나이: {age}세
- 성별: {sex}
- 상품유형: {product_type}
- 보험기간: {expiry_year}

데이터베이스 스키마:
{schema}
"""

# 기본 설정값 추가
DEFAULT_CONFIG = {
    "custom_name": "홍길동",
    "insu_age": 25,
    "sex": 1,  # 1: 남자, 0: 여자
    "product_type": "nr",  # nr: 무해지형, r: 해지환급형
    "expiry_year": "20y_100",
    "company_id": None  # None으로 설정하여 기본값 지정
}

def execute_sql_query(query: str, used_config: dict) -> Optional[list]:
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 설정값과 쿼리 출력
        print("\n=== 실행 결과 ===")
        print("\n[설정값]")
        print(f"이름: {used_config['custom_name']}")
        print(f"나이: {used_config['insu_age']}세")
        print(f"성별: {'남자' if used_config['sex'] == 1 else '여자'}")
        print(f"상품유형: {'무해지형' if used_config['product_type'] == 'nr' else '해지환급형'}")
        print(f"보험기간: {used_config['expiry_year']}")
        print(f"보험사ID: {used_config['company_id'] if used_config['company_id'] else '지정되지 않음'}")
        
        print("\n[실행 쿼리]")
        print(query)
        
        # 쿼리 실행
        cursor.execute(query)
        results = cursor.fetchall()
        
        print("\n[검색 결과]")
        if results:
            print(f"전체 결과 수: {len(results)}개")
            
            # query_results 디렉토리 생성
            os.makedirs('query_results', exist_ok=True)
            
            # 원본 결과를 임시 파일로 저장
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_filename = f'query_results/temp_result_{timestamp}.json'
            
            # 결과를 그대로 저장 (JSON 변환 없이)
            temp_data = {
                "설정값": used_config,
                "쿼리": query,
                "결과": [dict(row) for row in results]  # SQL 결과를 그대로 딕셔너리로 변환
            }
            
            with open(temp_filename, 'w', encoding='utf-8') as f:
                json.dump(temp_data, f, ensure_ascii=False, indent=2, default=str)
            
            print("\n임시 파일이 생성되었습니다:", temp_filename)
            
            # 결과 출력 (처음 20개만)
            for idx, row in enumerate(results[:20], 1):
                print(f"\n결과 {idx}:")
                for key, value in row.items():
                    print(f"{key}: {value}")
            
            print("\n2_json_converter.py를 실행하여 최종 JSON을 생성하세요.")
            
        else:
            print("검색 결과가 없습니다.")
        
        cursor.close()
        conn.close()
        return results
        
    except Exception as e:
        print(f"\n❌ SQL 실행 오류: {str(e)}")
        return None

def generate_sql_query(prompt: str, age: int, sex: int, product_type: str, expiry_year: str) -> str:
    try:
        client = openai.OpenAI()
        system_prompt = BASE_PROMPT.format(
            schema=DB_SCHEMA,
            age=age,
            sex_num=sex,
            sex='남자' if sex == 1 else '여자',
            product_type=product_type,
            expiry_year=expiry_year
        )
        
        response = client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        # SQL 쿼리 추출 및 정제
        sql_query = response.choices[0].message.content.strip()
        
        # 마크다운 코드 블록 제거
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        
        return sql_query
    except Exception as e:
        print(f"\n❌ GPT API 오류: {str(e)}")
        return None

def process_query(prompt: str):
    # 현재 사용되는 설정값 저장
    current_config = DEFAULT_CONFIG.copy()
    
    # 나이 추출 (숫자 + "세" 패턴)
    age_match = re.search(r'(\d+)세', prompt)
    if age_match:
        current_config["insu_age"] = int(age_match.group(1))
    
    # 성별 추출
    if "남성" in prompt or "남자" in prompt:
        current_config["sex"] = 1
    elif "여성" in prompt or "여자" in prompt:
        current_config["sex"] = 0
    
    # 상품유형 추출
    if "무해지" in prompt:
        current_config["product_type"] = "nr"
    elif "해지환급" in prompt:
        current_config["product_type"] = "r"
    
    # 보험기간 추출
    period_match = re.search(r'(\d+)년[/\s](\d+)세', prompt)
    if period_match:
        years = period_match.group(1)
        age = period_match.group(2)
        current_config["expiry_year"] = f"{years}y_{age}"
    
    # 보험사 추출 (옵션)
    if "삼성" in prompt:
        current_config["company_id"] = "01"
    elif "한화" in prompt:
        current_config["company_id"] = "02"
    # 다른 보험사들에 대한 매핑도 추가 가능
    
    sql_query = generate_sql_query(
        prompt=prompt,
        age=current_config["insu_age"],
        sex=current_config["sex"],
        product_type=current_config["product_type"],
        expiry_year=current_config["expiry_year"]
    )
    if sql_query:
        return execute_sql_query(sql_query, current_config)
    return None

def main():
    print("\n=== 보험 상담 챗봇 ===")
    print("\n기본 설정값:")
    print(f"이름: {DEFAULT_CONFIG['custom_name']}")
    print(f"나이: {DEFAULT_CONFIG['insu_age']}세")
    print(f"성별: {'남자' if DEFAULT_CONFIG['sex'] == 1 else '여자'}")
    print(f"상품유형: {'무해지형' if DEFAULT_CONFIG['product_type'] == 'nr' else '해지환급형'}")
    print(f"보험기간: {DEFAULT_CONFIG['expiry_year']}")
    print(f"보험사ID: {DEFAULT_CONFIG['company_id'] if DEFAULT_CONFIG['company_id'] else '지정되지 않음'}")
    
    while True:
        print("\n질문을 입력하세요 (종료하려면 'q' 또는 'quit' 입력):")
        question = input().strip()
        
        if question.lower() in ['q2_llm_to_sql.py', 'quit']:
            print("\n프로그램을 종료합니다.")
            break
            
        process_query(question)

if __name__ == "__main__":
    main()



