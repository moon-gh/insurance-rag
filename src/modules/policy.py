import os

from config.settings import settings
from db.sql_utils import TemplateManager
from models.search import search
from models.collection_loader import CollectionLoader
from models.embeddings import UpstageEmbedding
from models.generate_answer import generate_answer
from util.utils import find_matching_collections

from openai import OpenAI


class PolicyModule:
    def __init__(
        self,
        openai_client: OpenAI,
        template_manager: TemplateManager,
    ):
        self.openai_client = openai_client
        self.template_manager = template_manager
        self.vector_path = settings.vector_path
        self.collections: list = []  # TODO: 다시 확인
        self.loader = CollectionLoader(self.vector_path, UpstageEmbedding)
        # TODO: 외부에서 주입받아야 된다.

    def load_collections(self, user_question):
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

    def respond_policy_question(self, user_question: str) -> str:
        # TODO: 덩어리가 너무 크다. 하는일이 너무 많음. (시스템 디자인)
        self.load_collections(user_question)

        search_results = search(
            user_question, self.loader.collections, self.use_collections, top_k=2
        )

        answer = generate_answer(user_question, search_results, settings.openai_api_key)
        return answer
