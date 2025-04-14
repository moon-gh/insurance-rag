from dataclasses import asdict

from config.settings import Settings, settings
from db.schema import DB_SCHEMA
from options.enums import Sex

import simplejson as json
import mysql.connector
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader

openai_client = OpenAI()  # TODO: main 주입받도록 변경하기


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
        response = openai_client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "당신은 JSON 데이터 변환 전문가입니다. 주어진 예시 형식에 맞게 데이터를 변환해주세요.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
        )
        response_text = response.choices[0].message.content
        return response_text

    def convert(self, generate_json_data: dict) -> str:
        convert_prompt = self.template_manager.render("example_prompt.jinja2")
        converter_json_data = json.dumps(
            generate_json_data, ensure_ascii=False, indent=2, use_decimal=True
        )
        convert_json_prompt = convert_prompt + converter_json_data
        response = self.model(convert_json_prompt)
        json_str = response.replace("```json", "").replace("```", "").strip()
        return json_str


class SQLGenerator:
    """
    프롬프트와 설정값을 바탕으로 사용자의 기본정보를 추출
    """

    def __init__(self, template_manager: TemplateManager):
        self.template_manager = template_manager
        self.model_name = "gpt-4-0125-preview"

    def model(self, prompt: str):
        response = openai_client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self.generate_sql_system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        return response

    def generate(self, prompt: str, config: Settings) -> str:
        self.generate_sql_system_prompt = self.template_manager.render(
            "base_prompt.jinja2",
            schema=DB_SCHEMA,
            age=config.insu_age,
            sex_num=config.sex,
            sex="남자" if config.sex == Sex.MALE else "여자",
            product_type=config.product_type,
            expiry_year=config.expiry_year,
        )
        model = self.model(prompt)
        sql_query = model.choices[0].message.content.strip()
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        return sql_query


class QueryExecutor:
    def __init__(self, openai_client, template_manager: TemplateManager):
        self.db_client = DatabaseClient()
        self.json_converter = JSONConverter(openai_client, template_manager)

    def execute_sql_query(self, generated_sql: str, used_config: Settings) -> str:
        results = self.db_client.execute_query(generated_sql)
        print("\n[검색 결과]")
        if results:
            print(f"전체 결과 수: {len(results)}개")
            # 검색 결과와 설정값을 함께 딕셔너리로 구성
            temp_data = {
                "설정값": used_config.model_dump(),
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
