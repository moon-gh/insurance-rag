import logging

import chainlit as cl
from openai import OpenAI

from config.logger import setup_logging
from config.settings import PROJECT_ROOT, settings
from db.sql_utils import TemplateManager
from modules.user_state import UserState
from services.insurance_service import InsuranceService

setup_logging()
logger = logging.getLogger(__name__)
logging.info("\n=== 보험 상담 챗봇 ===")

template_manager = TemplateManager(templates_dir=PROJECT_ROOT / "prompts")
openai_client = OpenAI(api_key=settings.openai_api_key)
user_state = UserState()

insurance_service = InsuranceService(
    openai_client=openai_client, template_manager=template_manager, user_state=user_state
)


@cl.on_chat_start
async def start() -> None:
    actions = [
        cl.Action(
            name="m02_00",
            icon="mouse-pointer-click",
            payload={"value": "현대해상의 기본플랜 보험료를 알려줘"},
            label="현대해상의 기본플랜 보험료를 알려줘",
        ),
        cl.Action(
            name="m01_00",
            icon="mouse-pointer-click",
            payload={"value": "외상후 스트레스 장애(PTSD)를 보장하는 보험은?"},
            label="외상후 스트레스 장애(PTSD)를 보장하는 보험은?",
        ),
    ]

    await cl.Message(
        content="아래 버튼을 눌러 테스트 질문을 선택하거나 대화창에 질문을 입력해주세요.", actions=actions
    ).send()


@cl.action_callback("m01_00")
async def on_action_m01_00(action: cl.Action) -> None:
    await cl.Message(content=action.payload["value"]).send()
    await cl.Message(content=insurance_service.get_user_response(action.payload["value"])).send()


@cl.action_callback("m02_00")
async def on_action_m02_00(action: cl.Action) -> None:
    await cl.Message(content=action.payload["value"]).send()
    await cl.Message(content=insurance_service.get_user_response(action.payload["value"])).send()


@cl.on_message
async def main(message: cl.Message) -> None:
    await cl.Message(
        content=f"Insupanda Bot: {insurance_service.get_user_response(message.content)}",
    ).send()
