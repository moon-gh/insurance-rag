import sys
from pathlib import Path

from config.settings import PROJECT_ROOT, settings
from modules.intent import IntentModule
from modules.compare import CompareModule
from modules.policy import PolicyModule
from db.sql_utils import TemplateManager

from openai import OpenAI

# TODO: isort setting precommit setting


if __name__ == "__main__":
    print("\n=== 보험 상담 챗봇 ===")
    # TODO: 초기화문이 제일 위에 있어야함.
    template_manager = TemplateManager(templates_dir=PROJECT_ROOT / "prompts")
    openai_client = OpenAI(api_key=settings.openai_api_key)
    # TODO: main 더 쪼개기. 별도의 클래스를 짜서 별도의 manager가 처리하게 하기
    user_question = input(
        "질문을 입력하세요 (종료하려면 'q' 또는 'quit' 입력):\n"
    ).strip()
    if user_question in ["q", "quit", "exit"]:
        print("\n프로그램을 종료합니다.")
        sys.exit()

    # TODO: Unitest code 짜기
    classify_intent = IntentModule(openai_client, user_question, template_manager)
    policy_module = PolicyModule(openai_client, template_manager)
    compare_module = CompareModule(openai_client, template_manager)
    result_intent = classify_intent.classify_response()

    # TODO: 별도의 메소드? intent에 따라서... mediator pattern이나 factory pattern abc 클래스 상속받기
    if result_intent == "비교설계 질문":  # TODO: 비교설계 질문 enum으로 바꾸기
        print(result_intent)
        print(compare_module.get_search_result(user_question))
    else:
        print(result_intent)
        print(policy_module.respond_policy_question(user_question))
