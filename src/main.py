import os

from config.settings import PROJECT_ROOT, DEFAULT_CONFIG
from version01 import response
from util.utils import process_query
from DB.sql_utils import generate_sql_query, execute_sql_query

from jinja2 import Environment, FileSystemLoader
from openai import OpenAI

# TODO: isort setting precommit setting

env = Environment(loader=FileSystemLoader(PROJECT_ROOT / "prompts"))

openaai_key = os.environ["OPENAI_API_KEY"]


class IntentModule:
    def __init__(
        self,
        openai_client: OpenAI,
        user_question: str,
    ):
        self.openai_client = openai_client
        self.intent_template = env.get_template("intent_prompt.jinja2")
        self.intent_system_prompt = self.intent_template.render(question=user_question)

    def classify_response(self) -> str:
        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "너는 GA 보험설계사들이 사용하는 보험전문 챗봇이야.",
                },
                {"role": "user", "content": self.intent_system_prompt},
            ],
        )
        return response.choices[0].message.content


class CompareModule:
    def __init__(self):
        self.default_config = DEFAULT_CONFIG

    def print_settings(self, config) -> None:
        # TODO: config pydatic setting빼기. dataclass
        gender = "남자" if config["sex"] == 1 else "여자"
        product_type = "무해지형" if config["product_type"] == "nr" else "해지환급형"
        print("\n=== 실행 결과 ===")
        print("\n[설정값]")
        print(f"이름: {config['custom_name']}")
        print(f"나이: {config['insu_age']}세")
        print(f"성별: {gender}")
        print(f"상품유형: {product_type}")
        print(f"보험기간: {config['expiry_year']}")

    def get_search_result(self, user_question: str) -> str:
        # TODO: process_query, generate_sql_query 다 클래스화 시키고, 클래스 주입시켜야 함.
        # 클래스 상호 관계가 안맞는 것 같은데 맞춰야한다? 무슨말?
        prompt, current_config = process_query(user_question, self.default_config)
        generated_sql = generate_sql_query(prompt, current_config)
        self.print_settings(current_config)
        search_result = execute_sql_query(generated_sql, current_config)
        return search_result


if __name__ == "__main__":
    print("\n=== 보험 상담 챗봇 ===")

    user_question = input(
        "질문을 입력하세요 (종료하려면 'q' 또는 'quit' 입력):\n"
    ).strip()

    openai_client = OpenAI()
    classify_intent = IntentModule(openai_client, user_question)
    compare_module = CompareModule()
    result_intent = classify_intent.classify_response()

    if result_intent == "비교설계 질문":
        print(result_intent)
        print(compare_module.get_search_result(user_question))
    else:
        print("그 외 약관")
        response(user_question)
