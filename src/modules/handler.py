import os
from abc import ABC, abstractmethod

from config.settings import Settings, settings
from util.utils import process_query, find_matching_collections
from models.search import search
from models.collection_loader import CollectionLoader
from models.embeddings import UpstageEmbedding
from models.generate_answer import ResponseSearch
from db.sql_utils import TemplateManager, SQLGenerator, QueryExecutor
from options.enums import IntentType, ModelType

from openai import OpenAI


class Handler(ABC):
    def __init__(self, openai_client: OpenAI, template_manager: TemplateManager):
        self.openai_client = openai_client
        self.template_manager = template_manager

    @abstractmethod
    def handle(self, user_input: str) -> str:
        raise NotImplementedError("Handler should be implemented")


class IntentHandler(Handler):
    def __init__(self, openai_client: OpenAI, template_manager: TemplateManager):
        super().__init__(openai_client, template_manager)

    def handle(self, user_input: str) -> str:
        intent_template_prompt = self.template_manager.render(
            "intent_prompt.jinja2", question=user_input
        )
        response = self.openai_client.chat.completions.create(
            model=ModelType.INTENT_MODEL,
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
        execute_query: QueryExecutor,
        settings: Settings = settings,
    ):
        super().__init__(openai_client, template_manager)
        self.settings = settings
        self.sql_generator = SQLGenerator(openai_client, self.template_manager)
        self.execute_query = execute_query

    def print_settings(self, settings: Settings) -> None:
        print(repr(settings))

    def handle(self, user_input: str) -> str:
        prompt, current_settings = process_query(user_input, self.settings)
        self.settings = current_settings
        generated_sql = self.sql_generator.generate(prompt, self.settings)
        self.print_settings(self.settings)
        search_result = self.execute_query.execute_sql_query(
            generated_sql, self.settings
        )
        return search_result


class PolicyHandler(Handler):
    def __init__(self, openai_client: OpenAI, template_manager: TemplateManager):
        super().__init__(openai_client, template_manager)
        self.vector_path = settings.vector_path
        self.collections: list[str] = []
        self.loader = CollectionLoader(self.vector_path, UpstageEmbedding)
        self.response = ResponseSearch(settings.openai_client)

    def load_collections(self, user_input: str) -> None:
        available_collections = [
            collection_name
            for collection_name in os.listdir(self.loader.base_path)
            if os.path.isdir(os.path.join(self.loader.base_path, collection_name))
        ]

        self.use_collections = (
            self.collections
            if self.collections
            else find_matching_collections(user_input, available_collections)
        )

        for use_collection_name in self.use_collections:
            self.loader.load_collection(use_collection_name)

    def handle(self, user_input: str) -> str:
        self.load_collections(user_input)

        search_results = search(
            user_input, self.loader.collections, self.use_collections, top_k=2
        )

        answer = self.response.generate_answer(user_input, search_results)
        return answer


class HandlerFactory:
    @staticmethod
    def get_handler(
        intent: str, openai_client: OpenAI, template_manager: TemplateManager
    ) -> Handler:
        query_executor = QueryExecutor(openai_client, template_manager)
        if intent == IntentType.COMPARE_QUESTION:
            return CompareHandler(openai_client, template_manager, query_executor)
        if intent == IntentType.POLICY_QUESTION:
            return PolicyHandler(openai_client, template_manager)
        raise ValueError("올바른 intent type이 아닙니다.")
