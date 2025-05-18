from openai import OpenAI

from config.settings import Settings, settings
from db.sql_utils import (
    QueryExecutor,
    SQLGenerator,
    TemplateManager,
)
from util.utils import process_query


class CompareModule:
    def __init__(
        self,
        openai_client: OpenAI,
        template_manager: TemplateManager,
        config: Settings = settings,
    ):
        self.config = config
        self.template_manager = template_manager
        self.sql_generator = SQLGenerator(openai_client, self.template_manager)
        self.execute_query = QueryExecutor(openai_client, self.template_manager)

    def print_settings(self, config: Settings) -> None:
        gender = "남자" if config.sex == 1 else "여자"
        product_type = "무해지형" if config.product_type == "nr" else "해지환급형"
        print("\n=== 실행 결과 ===")
        print("\n[설정값]")
        print(f"이름: {config.custom_name}")
        print(f"나이: {config.insu_age}세")
        print(f"성별: {gender}")
        print(f"상품유형: {product_type}")
        print(f"보험기간: {config.expiry_year}")

    def get_search_result(self, user_question: str) -> str:
        prompt, current_config = process_query(user_question, self.config)
        self.config = current_config
        generated_sql = self.sql_generator.generate(prompt, self.config)
        self.print_settings(self.config)
        search_result = self.execute_query.execute_sql_query(generated_sql, self.config)
        return search_result
