from openai import OpenAI

from db.sql_utils import TemplateManager


class IntentModule:
    def __init__(
        self,
        openai_client: OpenAI,
        template_manager: TemplateManager,
    ):
        self.openai_client = openai_client
        self.template_manager = template_manager

    def classify_response(self, user_input: str) -> str:
        intent_template_prompt = self.template_manager.render("intent_prompt.jinja2", question=user_input)
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
