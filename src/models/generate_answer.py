from langchain.schema import SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from config.settings import settings


class PolicyResponse:
    def __init__(self, openai_client: str):
        if not openai_client:
            return "OpenAI API key가 제공되지 않았습니다. 환경 변수 OPENAI_API_KEY를 설정해주세요."
        self.openai_client = openai_client
        self.company_results = {}

    def extract_company_info(self, search_results: list[dict]) -> str:
        for result in search_results:
            collection_name = result.get("collection", "")
            self.company_results.setdefault(collection_name, []).append(result)

        self.multiple_companies = len(self.company_results) > 1

        context = ""
        for company, results in self.company_results.items():
            company_context = ""
            if self.multiple_companies:
                company_context += f"\n\n## {company} 정보:\n"
            for result in results:
                text = result.get("metadata", {}).get("text", "")
                if text:
                    company_context += f"\n---\n{text}"
            context += company_context
        return context

    def prompt_system(self) -> ChatPromptTemplate:
        system_prompt = "너는 보험 약관 전문가야. 항상 한국어로 대답해."
        if self.multiple_companies:
            system_prompt += " \
            사용자 질문에 '비교 | 차이 | 다른 | 다른점 | 비교해 | 비교해줘 | 차이점 | 알려줘 | 뭐가 더 나은가' 키워드가 있다면, \
            여러 보험사의 약관을 비교 분석하여 차이점과 공통점을 명확하게 설명해주세요. 표 형식으로 정리하면 좋습니다."

        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_prompt),
                ("human", "질문: {query}\n\n관련 문서: {context}\n\n답변:"),
            ]
        )
        return prompt

    def policy_model(self) -> ChatOpenAI:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.openai_client,
            temperature=0.7,
            max_tokens=2000,
        )
        return llm

    def generate_answer(self, user_input: str, search_results: list[dict]) -> str:
        if not search_results:
            return "검색 결과가 없습니다. 다른 질문을 시도해보세요."
        print("\n-------- 답변 생성 시작 --------")
        print(f"질문: '{user_input}'")
        print(f"검색 결과 수: {len(search_results)}")
        context = self.extract_company_info(search_results)
        if not context.strip():
            return "관련 정보를 찾을 수 없습니다. 더 구체적인 질문을 해주시거나, 다른 키워드를 사용해보세요."
        chain: Runnable = self.prompt_system() | self.policy_model() | StrOutputParser()
        response = chain.invoke({"query": user_input, "context": context})
        return response
