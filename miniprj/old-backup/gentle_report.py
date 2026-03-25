"""
Gentle Report Module

This module generates family-friendly reports for patient families using LangChain.
It translates clinical summaries into easy-to-understand language.
"""

import json
from typing import Any, Dict, Optional

from llm_service import LLMService, create_llm_service


class GentleReportGenerator:
    """Generate gentle reports for patient families"""

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize gentle report generator

        Args:
            llm_service: LLMService instance (creates new one if not provided)
        """
        self.llm_service = llm_service or create_llm_service()
        self.chain = self.llm_service.create_gentle_report_chain()

    def generate_report(
        self,
        patient_id: str,
        risk_level: str,
        clinical_summary: str,
        key_changes: str,
        approved_by: Optional[str] = None,
        require_approval: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate gentle report for patient family

        Args:
            patient_id: Patient identifier
            risk_level: Risk level (high/medium/low)
            clinical_summary: Clinical summary text
            key_changes: Key changes in patient condition
            approved_by: Medical staff who approved this report (required if require_approval=True)
            require_approval: Whether medical staff approval is required (default: True)

        Returns:
            Gentle report dictionary with status, explanation, expectations, and guidance
        """
        # Check approval requirement
        if require_approval and not approved_by:
            return {
                "patient_id": patient_id,
                "status": "error",
                "error": "의료진 승인이 필요합니다. approved_by 파라미터를 제공하세요.",
                "approved": False,
            }

        try:
            # Run the chain using LCEL
            result = self.chain.invoke(
                {
                    "patient_id": patient_id,
                    "risk_level": risk_level,
                    "clinical_summary": clinical_summary,
                    "key_changes": key_changes,
                }
            )

            # Result is already parsed by PydanticOutputParser
            return {
                "patient_id": patient_id,
                "status": result.status,
                "simple_explanation": result.simple_explanation,
                "what_to_expect": result.what_to_expect,
                "family_guidance": result.family_guidance,
                "approved_by": approved_by,
                "approved": True,
                "timestamp": None,  # Add server timestamp in API layer
            }
        except Exception as e:
            # Fallback response on error
            return {
                "patient_id": patient_id,
                "status": "error",
                "simple_explanation": "환자 상태 리포트 생성 중 오류가 발생했습니다.",
                "what_to_expect": "담당 의료진께 직접 문의해주세요.",
                "family_guidance": "간호사실 또는 주치의와 상담을 요청하시기 바랍니다.",
                "approved_by": approved_by,
                "approved": False,
                "error": str(e),
            }

    def generate_from_clinical_summary(
        self,
        clinical_summary_output: Dict[str, Any],
        approved_by: Optional[str] = None,
        require_approval: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate gentle report directly from clinical summary output

        Args:
            clinical_summary_output: Output from ClinicalSummaryGenerator
            approved_by: Medical staff who approved this report
            require_approval: Whether medical staff approval is required

        Returns:
            Gentle report dictionary
        """
        patient_id = clinical_summary_output.get("patient_id", "unknown")
        risk_level = clinical_summary_output.get("risk_level", "unknown")
        summary = clinical_summary_output.get("summary", "")

        # Extract key changes from key_features
        key_features = clinical_summary_output.get("key_features", [])
        if key_features:
            key_changes = ", ".join(
                [f"{f.get('feature')}: {f.get('value')}" for f in key_features]
            )
        else:
            key_changes = "주요 변화 없음"

        return self.generate_report(
            patient_id=patient_id,
            risk_level=risk_level,
            clinical_summary=summary,
            key_changes=key_changes,
            approved_by=approved_by,
            require_approval=require_approval,
        )


def create_gentle_report_generator(
    llm_service: Optional[LLMService] = None,
) -> GentleReportGenerator:
    """
    Factory function to create GentleReportGenerator

    Args:
        llm_service: Optional LLMService instance

    Returns:
        GentleReportGenerator instance
    """
    return GentleReportGenerator(llm_service=llm_service)


if __name__ == "__main__":
    # Test gentle report generation
    print("Testing Gentle Report Generator...")

    generator = create_gentle_report_generator()

    # Sample clinical summary
    sample_clinical = {
        "patient_id": "demo_001",
        "risk_level": "high",
        "summary": "지난 4시간 동안 평균동맥압(MAP) 하락, 젖산(Lactate) 수치 상승, 소변량 감소가 관찰되었습니다. 이에 따라 12시간 내 Pressors_start 위험도가 85%로 상승했습니다.",
        "key_features": [
            {"feature": "평균동맥압", "value": "58 mmHg"},
            {"feature": "젖산 수치", "value": "4.2 mmol/L"},
            {"feature": "소변량", "value": "0.3 ml/kg/hr"},
        ],
    }

    # Test 1: Without approval (should fail)
    print("\nTest 1: Without approval")
    report = generator.generate_from_clinical_summary(sample_clinical)
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # Test 2: With approval
    print("\nTest 2: With approval")
    report = generator.generate_from_clinical_summary(
        sample_clinical, approved_by="Dr. Kim"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
