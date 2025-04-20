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

    user_question = input(
        "질문을 입력하세요 (종료하려면 'q' 또는 'quit' 입력):\n"
    ).strip()
    if user_question in ["q", "quit", "exit"]:
        print("\n프로그램을 종료합니다.")
        sys.exit()

    template_manager = TemplateManager(
        templates_dir=Path(str(f"{PROJECT_ROOT}/prompts"))
    )
    openai_client = OpenAI(api_key=settings.openai_api_key)
    classify_intent = IntentModule(openai_client, user_question, template_manager)
    policy_module = PolicyModule(openai_client, template_manager)
    compare_module = CompareModule(openai_client, template_manager)
    result_intent = classify_intent.classify_response()

    if result_intent == "비교설계 질문":
        print(result_intent)
        print(compare_module.get_search_result(user_question))
    else:
        print(result_intent)
        print(policy_module.respond_policy_question(user_question))
