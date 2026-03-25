"""
LLM Service Module using LangChain

This module provides core LLM functionality using LangChain framework:
- ChatOpenAI model initialization
- Prompt template management
- Output parsers
"""

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()


class ClinicalSummaryOutput(BaseModel):
    """Output schema for clinical summary"""

    risk_level: str = Field(description="위험도 수준 (high/medium/low)")
    risk_score: float = Field(description="위험도 점수 (0-1)")
    summary: str = Field(description="임상 상황 요약")
    key_features: List[Dict[str, Any]] = Field(
        description="근거 피처 목록 (최대 3개)"
    )
    recommended_actions: List[str] = Field(
        description="권장 확인 항목 (최대 3개)"
    )
    data_quality_alerts: List[str] = Field(
        description="데이터 품질 경고 사항", default_factory=list
    )


class GentleReportOutput(BaseModel):
    """Output schema for gentle report"""

    status: str = Field(description="환자 상태 (안정/불안정/매우 불안정)")
    simple_explanation: str = Field(description="쉬운 언어로 작성된 상태 설명")
    what_to_expect: str = Field(description="예상되는 상황 설명")
    family_guidance: str = Field(description="보호자 안내 사항")


class QueryFilterOutput(BaseModel):
    """Output schema for Q&A query filters"""

    filters: Dict[str, Any] = Field(description="필터 파라미터")
    interpretation: str = Field(description="질의 해석 설명")
    sort_by: Optional[str] = Field(description="정렬 기준", default=None)


class LLMService:
    """Core LLM service using LangChain"""

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.2,
        api_key: Optional[str] = None,
    ):
        """
        Initialize LLM service

        Args:
            model_name: OpenAI model name (default: from env or gpt-4o-mini)
            temperature: LLM temperature
            api_key: OpenAI API key (default: from env)
        """
        self.model_name = model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")

        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=temperature,
            openai_api_key=self.api_key,
        )

    def create_clinical_summary_chain(self):
        """
        Create LangChain chain for clinical summary generation using LCEL

        Returns:
            Runnable chain for clinical summary
        """
        parser = PydanticOutputParser(pydantic_object=ClinicalSummaryOutput)

        template = """당신은 중환자실 전문의를 돕는 임상 의사결정 지원 AI입니다.

환자의 생체 신호(vitals), 검사 결과(labs), 그리고 모델 예측 결과를 분석하여 
의료진이 빠르게 파악할 수 있는 임상 요약을 생성하세요.

**입력 데이터:**
- 환자 ID: {patient_id}
- Vitals 트렌드: {vitals}
- Labs 결과: {labs}
- SHAP Top Features: {shap_features}
- 데이터 품질 플래그: {data_quality_flags}
- 예측 위험도: {prediction_risk}

**출력 요구사항:**
1. 위험도 수준 (high/medium/low) 및 점수 제시
2. 지난 수시간 동안의 주요 변화 요약 (2-3문장)
3. 위험도에 기여한 핵심 피처 3개 (SHAP 기반)
4. 의료진이 확인해야 할 권장 항목 3개
5. 데이터 품질 이상이 있으면 명시

{format_instructions}
"""

        prompt = PromptTemplate(
            template=template,
            input_variables=[
                "patient_id",
                "vitals",
                "labs",
                "shap_features",
                "data_quality_flags",
                "prediction_risk",
            ],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        # Use LCEL (LangChain Expression Language)
        chain = prompt | self.llm | parser
        return chain

    def create_gentle_report_chain(self):
        """
        Create LangChain chain for gentle report generation using LCEL

        Returns:
            Runnable chain for gentle report
        """
        parser = PydanticOutputParser(pydantic_object=GentleReportOutput)

        template = """당신은 환자 보호자에게 환자의 상태를 설명하는 의료 커뮤니케이터입니다.

의료진용 임상 요약을 기반으로, 보호자가 이해하기 쉬운 언어로 환자 상태를 설명하세요.

**원칙:**
- 의학 용어를 최소화하고 일반인이 이해할 수 있는 단어 사용
- 불안감을 과도하게 조성하지 않되, 정확한 상황 전달
- 보호자가 준비해야 할 사항이 있으면 부드럽게 안내
- 의료진이 환자를 집중 치료 중임을 명시

**입력 데이터:**
- 환자 ID: {patient_id}
- 위험도 수준: {risk_level}
- 임상 요약: {clinical_summary}
- 주요 변화: {key_changes}

**출력 요구사항:**
1. 환자 상태 (안정/불안정/매우 불안정)
2. 쉬운 언어로 작성된 상태 설명 (의학 용어 최소화)
3. 예상되는 상황 설명
4. 보호자 안내 사항 (예: 환자 곁 지킬 준비, 의료진 문의 사항 등)

{format_instructions}
"""

        prompt = PromptTemplate(
            template=template,
            input_variables=[
                "patient_id",
                "risk_level",
                "clinical_summary",
                "key_changes",
            ],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        # Use LCEL
        chain = prompt | self.llm | parser
        return chain

    def create_qa_filter_chain(self):
        """
        Create LangChain chain for Q&A filter generation using LCEL

        Returns:
            Runnable chain for Q&A filter
        """
        parser = PydanticOutputParser(pydantic_object=QueryFilterOutput)

        template = """당신은 자연어 질의를 환자 필터 쿼리로 변환하는 AI입니다.

사용자의 자연어 질문을 분석하여, 환자 목록을 필터링할 수 있는 파라미터로 변환하세요.

**Few-shot 예시:**

질의: "최근 2시간 내 위험도 급상승한 환자 보여줘"
→ filters: {{"time_range": "2h", "risk_change": "급상승", "threshold": "any"}}
   interpretation: "최근 2시간 동안 위험도가 급격히 상승한 환자를 조회합니다."
   sort_by: "risk_change_rate"

질의: "Pressor 위험 상위 5명"
→ filters: {{"risk_type": "pressor", "top_n": 5}}
   interpretation: "Pressor 시작 위험도가 가장 높은 상위 5명의 환자를 조회합니다."
   sort_by: "pressor_risk"

질의: "사망 위험 높은 환자"
→ filters: {{"risk_type": "mortality", "risk_level": "high"}}
   interpretation: "사망 위험도가 높은 수준인 환자를 조회합니다."
   sort_by: "mortality_risk"

**사용자 질의:**
{query}

**사용 가능한 필터 옵션:**
- time_range: "1h", "2h", "4h", "12h", "24h"
- risk_type: "mortality", "pressor", "vent"
- risk_level: "high", "medium", "low"
- risk_change: "급상승", "상승", "안정", "하락"
- top_n: 정수 (상위 N명)

{format_instructions}
"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        # Use LCEL
        chain = prompt | self.llm | parser
        return chain


def create_llm_service(
    model_name: Optional[str] = None,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
) -> LLMService:
    """
    Factory function to create LLMService instance

    Args:
        model_name: OpenAI model name
        temperature: LLM temperature
        api_key: OpenAI API key

    Returns:
        Initialized LLMService instance
    """
    return LLMService(model_name=model_name, temperature=temperature, api_key=api_key)


if __name__ == "__main__":
    # Test LLM service initialization
    service = create_llm_service()
    print("✅ LLM Service initialized successfully")
    print(f"Model: {service.model_name}")

    # Test chain creation
    clinical_chain = service.create_clinical_summary_chain()
    print("✅ Clinical Summary Chain created")

    gentle_chain = service.create_gentle_report_chain()
    print("✅ Gentle Report Chain created")

    qa_chain = service.create_qa_filter_chain()
    print("✅ Q&A Filter Chain created")
