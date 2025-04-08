from config.settings import DB_CONFIG, PROJECT_ROOT
from DB.schema import DB_SCHEMA

import simplejson as json
import mysql.connector
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader

openai_client = OpenAI()
env = Environment(loader=FileSystemLoader(PROJECT_ROOT / "prompts"))
conn = mysql.connector.connect(**DB_CONFIG)


def convert_sql_to_json_format(generate_json_data: dict) -> str:
    convert_prompt = env.get_template("example_prompt.jinja2").render()

    converter_json_data = json.dumps(
        generate_json_data, ensure_ascii=False, indent=2, use_decimal=True
    )

    convert_json_prompt = convert_prompt + converter_json_data
    response = openai_client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=[
            {
                "role": "system",
                "content": "당신은 JSON 데이터 변환 전문가입니다. 주어진 예시 형식에 맞게 데이터를 변환해주세요.",
            },
            {"role": "user", "content": convert_json_prompt},
        ],
        temperature=0,
    )
    response_text = response.choices[0].message.content

    json_str = (
        response_text.replace("```json", "").replace("```", "").strip()
    )  # TODO: anti pattern, json type을 보장하는 openai 명세가 따로 있음.
    return json_str


def execute_sql_query(generated_sql: str, used_config: dict) -> str:
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(generated_sql)
        results = cursor.fetchall()

        print("\n[검색 결과]")
        if results:
            print(f"전체 결과 수: {len(results)}개")

            # 결과를 그대로 저장 JSON 변환 없이 그대로 딕셔너리로 변환
            temp_data = {
                "설정값": used_config,
                "쿼리": generated_sql,
                "결과": [dict(row) for row in results],
            }

            json_result = convert_sql_to_json_format(temp_data)
            return json_result
        else:
            print("검색 결과가 없습니다.")
        return results


def generate_sql_query(prompt, config) -> str:
    generate_sql_template = env.get_template("base_prompt.jinja2")
    generate_sql_system_prompt = generate_sql_template.render(
        schema=DB_SCHEMA,
        age=config["insu_age"],
        sex_num=config["sex"],
        sex="남자" if config["sex"] == 1 else "여자",
        product_type=config["product_type"],
        expiry_year=config["expiry_year"],
    )

    response = openai_client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=[
            {"role": "system", "content": generate_sql_system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    # SQL 쿼리 추출 및 정제
    sql_query = response.choices[0].message.content.strip()

    # 마크다운 코드 블록 제거
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

    return sql_query
