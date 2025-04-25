from abc import ABC, abstractmethod

from modules.compare import CompareModule
from modules.policy import PolicyModule
from db.sql_utils import TemplateManager
from options.enums import IntentType

from openai import OpenAI


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
