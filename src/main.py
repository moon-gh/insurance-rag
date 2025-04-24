import sys
from abc import ABC, abstractmethod

from config.settings import PROJECT_ROOT, settings
from modules.intent import IntentModule
from modules.compare import CompareModule
from modules.policy import PolicyModule
from db.sql_utils import TemplateManager
from options.enums import IntentType

from openai import OpenAI


# TODO: isort setting precommit setting
class Handler(ABC):
    @abstractmethod
    def handle(self, question: str) -> str:
        pass


class CompareHandler(Handler):
    def __init__(self, llm_client: OpenAI, template_manager: TemplateManager):
        self.compare_module = CompareModule(llm_client, template_manager)

    def handle(self, question: str) -> str:
        return self.compare_module.get_search_result(question)


class PolicyHandler(Handler):
    def __init__(self, llm_client: OpenAI, template_manager: TemplateManager):
        self.policy_module = PolicyModule(llm_client, template_manager)

    def handle(self, question: str) -> str:
        return self.policy_module.respond_policy_question(question)


class HandlerFactory:
    @staticmethod
    def get_handler(
        intent: str, llm_client: OpenAI, template_manager: TemplateManager
    ) -> Handler:
        if intent == IntentType.COMPARE_QUESTION:
            return CompareHandler(llm_client, template_manager)
        return PolicyHandler(llm_client, template_manager)


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
