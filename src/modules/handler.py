import os
from abc import ABC, abstractmethod

from openai import OpenAI

from config.settings import UserState, settings, user_state
from db.sql_utils import QueryExecutor, SQLGenerator, TemplateManager
from models.collection_loader import CollectionLoader
from models.embeddings import UpstageEmbedding
from models.generate_answer import PolicyResponse
from models.search import search
from options.enums import IntentType, ModelType
from util.utils import QueryInfoExtract, find_matching_collections


class Handler(ABC):
    def __init__(self, openai_client: OpenAI, template_manager: TemplateManager):
        self.openai_client = openai_client
        self.template_manager = template_manager

    @abstractmethod
    def handle(self, user_input: str) -> str:
        raise NotImplementedError("Handler should be implemented")


class IntentHandler(Handler):
    system_prompt = "너는 GA 보험설계사들이 사용하는 보험전문 챗봇이야."

    def __init__(self, openai_client: OpenAI, template_manager: TemplateManager):
        super().__init__(openai_client, template_manager)

    def handle(self, user_input: str) -> str:
        intent_template_prompt = self.template_manager.render("intent_prompt.jinja2", question=user_input)
        response = self.openai_client.chat.completions.create(
            model=ModelType.INTENT_MODEL,
            messages=[
                {"role": "system", "content": self.system_prompt},
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
        sql_generator: SQLGenerator,
        user_state: UserState = user_state,
    ):
        super().__init__(openai_client, template_manager)
        self.user_state = user_state
        self.sql_generator = sql_generator
        self.execute_query = execute_query

    def print_settings(self, user_state: UserState) -> None:
        print(repr(user_state))

    def handle(self, user_input: str) -> str:
        process_query = QueryInfoExtract(user_input, self.user_state)
        prompt, curr_user_state = process_query.process()
        self.user_state = curr_user_state
        generated_sql = self.sql_generator.generate(prompt, self.user_state)
        self.print_settings(self.user_state)
        search_result = self.execute_query.execute_sql_query(generated_sql, self.user_state)
        return search_result


class PolicyHandler(Handler):
    def __init__(
        self,
        openai_client: OpenAI,
        template_manager: TemplateManager,
        collection_loader: CollectionLoader,
        response_policy: PolicyResponse,
    ):
        super().__init__(openai_client, template_manager)
        self.collections: list[str] = []
        self.loader = collection_loader
        self.response_policy = response_policy

    def load_collections(self, user_input: str) -> None:
        available_collections = [
            collection_name
            for collection_name in os.listdir(self.loader.base_path)
            if os.path.isdir(os.path.join(self.loader.base_path, collection_name))
        ]

        self.use_collections = (
            self.collections if self.collections else find_matching_collections(user_input, available_collections)
        )

        for use_collection_name in self.use_collections:
            self.loader.load_collection(use_collection_name)

    def handle(self, user_input: str) -> str:
        self.load_collections(user_input)

        search_results = search(user_input, self.loader.collections, self.use_collections, top_k=2)

        answer = self.response_policy.generate_answer(user_input, search_results)
        return answer


class HandlerFactory:
    @staticmethod
    def get_handler(intent: str, openai_client: OpenAI, template_manager: TemplateManager) -> Handler:
        generate_sql_query = SQLGenerator(openai_client, template_manager)
        query_executor = QueryExecutor(openai_client, template_manager)
        collection_loader = CollectionLoader(settings.vector_path, UpstageEmbedding)
        response_policy = PolicyResponse(openai_client)
        if intent == IntentType.COMPARE_QUESTION:
            return CompareHandler(openai_client, template_manager, query_executor, generate_sql_query)
        if intent == IntentType.POLICY_QUESTION:
            return PolicyHandler(openai_client, template_manager, collection_loader, response_policy)
        raise ValueError("올바른 intent type이 아닙니다.")
