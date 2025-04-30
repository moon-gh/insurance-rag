import os
from abc import ABC, abstractmethod

from config.settings import Settings, settings
from util.utils import process_query
from util.utils import find_matching_collections
from models.search import search
from models.collection_loader import CollectionLoader
from models.embeddings import UpstageEmbedding
from models.generate_answer import generate_answer
from modules.policy import PolicyModule
from db.sql_utils import (
    TemplateManager,
    SQLGenerator,
    QueryExecutor,
)
from options.enums import IntentType

from openai import OpenAI


class Handler(ABC):
    @abstractmethod
    def handle(self, user_input: str) -> str:
        raise NotImplementedError("Handler should be implemented")


class IntentHandler(Handler):
    def __init__(self, openai_client: OpenAI, template_manager: TemplateManager):
        self.openai_client = openai_client
        self.template_manager = template_manager

    def handle(self, user_input: str) -> str:
        intent_template_prompt = self.template_manager.render(
            "intent_prompt.jinja2", question=user_input
        )
        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "너는 GA 보험설계사들이 사용하는 보험전문 챗봇이야.",
                },
                {"role": "user", "content": intent_template_prompt},
            ],
        )
        return response.choices[0].message.content


class CompareHandler(Handler):
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

    def handle(self, user_input: str) -> str:
        prompt, current_config = process_query(user_input, self.config)
        self.config = current_config
        generated_sql = self.sql_generator.generate(prompt, self.config)
        self.print_settings(self.config)
        search_result = self.execute_query.execute_sql_query(generated_sql, self.config)
        return search_result


class PolicyHandler(Handler):
    def __init__(self, openai_client: OpenAI, template_manager: TemplateManager):
        self.openai_client = openai_client
        self.template_manager = template_manager
        self.vector_path = settings.vector_path
        self.collections: list = []  # TODO: 다시 확인
        self.loader = CollectionLoader(self.vector_path, UpstageEmbedding)

    def load_collections(self, user_question: str) -> bool:
        available_collections = [
            collection_name
            for collection_name in os.listdir(self.loader.base_path)
            if os.path.isdir(os.path.join(self.loader.base_path, collection_name))
        ]

        self.use_collections = (
            self.collections
            if self.collections
            else find_matching_collections(user_question, available_collections)
        )

        for use_collection_name in self.use_collections:
            self.loader.load_collection(use_collection_name)
        return True

    def handle(self, user_input: str) -> str:
        self.load_collections(user_input)

        search_results = search(
            user_input, self.loader.collections, self.use_collections, top_k=2
        )

        answer = generate_answer(user_input, search_results, settings.openai_api_key)
        return answer


class HandlerFactory:
    @staticmethod
    def get_handler(
        intent: str, openai_client: OpenAI, template_manager: TemplateManager
    ) -> Handler:
        if intent == IntentType.COMPARE_QUESTION:
            return CompareHandler(openai_client, template_manager)
        return PolicyHandler(openai_client, template_manager)
