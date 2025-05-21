from openai import OpenAI

from config.settings import PROJECT_ROOT, settings
from db.sql_utils import TemplateManager
from services.insurance_service import InsuranceService

if __name__ == "__main__":
    print("\n=== 보험 상담 챗봇 ===")

    template_manager = TemplateManager(templates_dir=PROJECT_ROOT / "prompts")
    openai_client = OpenAI(api_key=settings.openai_api_key)

    insurance_service = InsuranceService(openai_client=openai_client, template_manager=template_manager)
    insurance_service.run()
