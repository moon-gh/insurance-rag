import json
from dataclasses import asdict

import mysql.connector
from jinja2 import Environment, FileSystemLoader

from config.settings import Settings, UserState, settings
from db.schema import DB_SCHEMA
from options.enums import Sex


class TemplateManager:
    """
    템플릿 관리 클래스
    """

    def __init__(self, templates_dir):
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def render(self, template_name: str, **kwargs) -> str:
        template = self.env.get_template(template_name)
        return template.render(**kwargs)


class DatabaseClient:
    def __init__(self, settings: Settings = settings):
        self.conn = mysql.connector.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_database,
        )

    def execute_query(self, query: str) -> list:
        with self.conn.cursor(dictionary=True) as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
        return results

    def close(self):
        self.conn.close()


class JSONConverter:
    def __init__(
        self,
        openai_client,
        template_manager: TemplateManager,
        model_name: str = "gpt-4-0125-preview",
        temperature: float = 0.0,
    ):
        self.openai_client = openai_client
        self.template_manager = template_manager
        self.model_name = model_name
        self.temperature = temperature

    def model(self, prompt: str):
        response = self.openai_client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "당신은 JSON 데이터 변환 전문가입니다. 주어진 예시 형식에 맞게 데이터를 변환해주세요.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            response_format={"type": "json_object"},
        )
        response_text = response.choices[0].message.content
        return response_text

    def convert(self, generate_json_data: dict) -> str:
        convert_prompt = self.template_manager.render("example_prompt.jinja2")
        converter_json_data = json.dumps(generate_json_data, ensure_ascii=False, indent=2, use_decimal=True)
        convert_json_prompt = convert_prompt + converter_json_data
        response = self.model(convert_json_prompt)
        return response


class SQLGenerator:
    """
    프롬프트에 있는 사용자 정보를 추출해 관련 보험을 조회하는 SQL 쿼리생성
    """

    def __init__(self, openai_client, template_manager: TemplateManager):
        self.openai_client = openai_client
        self.template_manager = template_manager
        self.model_name = "gpt-4-0125-preview"

    def model(self, prompt: str):
        response = self.openai_client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self.generate_sql_system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            response_format={"type": "text"},
        )
        return response

    def generate(self, prompt: str, user_state: UserState) -> str:
        self.generate_sql_system_prompt = self.template_manager.render(
            "base_prompt.jinja2",
            schema=DB_SCHEMA,
            age=user_state.insu_age,
            sex_num=user_state.insu_sex,
            sex="남자" if user_state.insu_sex == Sex.MALE else "여자",
            product_type=user_state.product_type,
            expiry_year=user_state.expiry_year,
        )
        model = self.model(prompt)
        sql_query = model.choices[0].message.content.strip()
        return sql_query


class QueryExecutor:
    def __init__(self, openai_client, template_manager: TemplateManager):
        self.db_client = DatabaseClient()
        self.json_converter = JSONConverter(openai_client, template_manager)

    def execute_sql_query(self, generated_sql: str, user_state: UserState) -> str:
        results = self.db_client.execute_query(generated_sql)
        print("\n[검색 결과]")
        if results:
            print(f"전체 결과 수: {len(results)}개")
            # 검색 결과와 설정값을 함께 딕셔너리로 구성
            temp_data = {
                "설정값": asdict(user_state),
                "쿼리": generated_sql,
                "결과": results,  # 각 행은 이미 딕셔너리 형태임
            }
            # 변환된 JSON 결과를 반환
            print()
            json_result = self.json_converter.convert(temp_data)
            return json_result
        else:
            print("검색 결과가 없습니다.")
            return json.dumps([])
