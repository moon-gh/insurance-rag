from openai import OpenAI

from db.sql_utils import TemplateManager
from modules.handler import HandlerFactory, IntentHandler
from modules.user_state import UserState
from options.enums import ConversationFlow


class InsuranceService:
    def __init__(self, openai_client: OpenAI, template_manager: TemplateManager, user_state: UserState):
        self.openai_client = openai_client
        self.template_manager = template_manager
        self.user_state = user_state

    def __get_user_input(self) -> str:
        return input("질문을 입력하세요 (종료하려면 'q', 'quit', 'exit' 입력):\n").strip()

    def __handle_user_input(self, user_input: str) -> None:
        flow = ConversationFlow.ENTRY
        intent_handler = IntentHandler(self.openai_client, self.template_manager)
        intent = intent_handler.handle(user_input)

        while flow is not ConversationFlow.END:
            handler = HandlerFactory.get_handler(intent, self.openai_client, self.template_manager, self.user_state)
            response = handler.handle(user_input)
            print(response)

    def run(self) -> None:
        user_input = self.__get_user_input()
        self.__handle_user_input(user_input)
