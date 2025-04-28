from abc import ABC, abstractmethod

from modules.intent import IntentModule
from modules.compare import CompareModule
from modules.policy import PolicyModule
from db.sql_utils import TemplateManager
from options.enums import IntentType

from openai import OpenAI


class Handler(ABC):
    @abstractmethod
    def handle(self, question: str) -> str:
        pass


class IntentHandler(Handler):
    def __init__(self, openai_client: OpenAI, template_manager: TemplateManager):
        self.intent_module = IntentModule(openai_client, template_manager)

    def handle(self, question: str) -> str:
        return self.intent_module.classify_response(question)


class CompareHandler(Handler):
    def __init__(self, openai_client: OpenAI, template_manager: TemplateManager):
        self.compare_module = CompareModule(openai_client, template_manager)

    def handle(self, question: str) -> str:
        return self.compare_module.get_search_result(question)


class PolicyHandler(Handler):
    def __init__(self, openai_client: OpenAI, template_manager: TemplateManager):
        self.policy_module = PolicyModule(openai_client, template_manager)

    def handle(self, question: str) -> str:
        return self.policy_module.respond_policy_question(question)


class HandlerFactory:
    @staticmethod
    def get_handler(
        intent: str, openai_client: OpenAI, template_manager: TemplateManager
    ) -> Handler:
        print("aaaa", intent)
        if intent == IntentType.COMPARE_QUESTION:
            return CompareHandler(openai_client, template_manager)
        return PolicyHandler(openai_client, template_manager)
