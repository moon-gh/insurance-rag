import logging

from openai import OpenAI

from config.logger import setup_logging
from config.settings import PROJECT_ROOT, settings
from db.sql_utils import TemplateManager
from modules.user_state import UserState
from services.insurance_service import InsuranceService

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    logging.info("\n=== 보험 상담 챗봇 ===")

    template_manager = TemplateManager(templates_dir=PROJECT_ROOT / "prompts")
    openai_client = OpenAI(api_key=settings.openai_api_key)
    user_state = UserState()

    insurance_service = InsuranceService(
        openai_client=openai_client, template_manager=template_manager, user_state=user_state
    )
    insurance_service.run()
