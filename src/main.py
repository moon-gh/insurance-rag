import sys

from config.settings import PROJECT_ROOT, settings
from modules.intent import IntentModule
from db.sql_utils import TemplateManager
from modules.handler import HandlerFactory

from openai import OpenAI


# TODO: isort setting precommit setting

if __name__ == "__main__":
    print("\n=== 보험 상담 챗봇 (Factory Pattern) ===")

    template_manager = TemplateManager(templates_dir=PROJECT_ROOT / "prompts")
    openai_client = OpenAI(api_key=settings.openai_api_key)

    user_question = input(
        "질문을 입력하세요 (종료하려면 'q', 'quit', 'exit' 입력):\n"
    ).strip()
    if user_question in ["q", "quit", "exit"]:
        print("\n프로그램을 종료합니다.")
        sys.exit()

    intent = IntentModule(
        openai_client, user_question, template_manager
    ).classify_response()
    print(f"[Intent]: {intent}")

    handler = HandlerFactory.get_handler(intent, openai_client, template_manager)
    response = handler.handle(user_question)
    print(response)
