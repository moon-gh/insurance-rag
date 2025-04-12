import os
from pathlib import Path

from config.settings import PROJECT_ROOT
from util.utils import process_query
from modules.intent import IntentModule
from modules.compare import CompareModule
from DB.sql_utils import TemplateManager

from openai import OpenAI
from version01 import response

# TODO: isort setting precommit setting

template_manager = TemplateManager(templates_dir=Path(str(f"{PROJECT_ROOT}/prompts")))

openaai_key = os.environ["OPENAI_API_KEY"]


if __name__ == "__main__":
    print("\n=== 보험 상담 챗봇 ===")

    user_question = input(
        "질문을 입력하세요 (종료하려면 'q' 또는 'quit' 입력):\n"
    ).strip()

    openai_client = OpenAI()
    classify_intent = IntentModule(openai_client, user_question, template_manager)
    compare_module = CompareModule(openai_client, template_manager)
    result_intent = classify_intent.classify_response()

    if result_intent == "비교설계 질문":
        print(result_intent)
        print(compare_module.get_search_result(user_question))
    else:
        print("그 외 약관")
        response(user_question)
