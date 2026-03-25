"""
Clinical Summary Module

This module generates clinical summaries for medical staff using LangChain.
It analyzes patient vitals, labs, and model predictions to create actionable insights.
"""

import json
from typing import Any, Dict, List, Optional

from llm_service import LLMService, create_llm_service


class ClinicalSummaryGenerator:
    """Generate clinical summaries for medical staff"""

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize clinical summary generator

        Args:
            llm_service: LLMService instance (creates new one if not provided)
        """
        self.llm_service = llm_service or create_llm_service()
        self.chain = self.llm_service.create_clinical_summary_chain()

    def generate_summary(
        self,
        patient_id: str,
        vitals: Dict[str, Any],
        labs: Dict[str, Any],
        shap_features: List[Dict[str, Any]],
        prediction_risk: Dict[str, float],
        data_quality_flags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate clinical summary for a patient

        Args:
            patient_id: Patient identifier
            vitals: Vitals trend data (e.g., {"map": 58, "sbp": 82, "hr": 120})
            labs: Lab results (e.g., {"lactate": 4.2, "wbc": 18})
            shap_features: SHAP top features with contributions
                [{"feature": "map_mean", "value": 58, "contribution": -0.35}, ...]
            prediction_risk: Prediction risks by outcome type
                {"mortality": 0.75, "pressor": 0.85, "vent": 0.45}
            data_quality_flags: List of data quality issues (optional)

        Returns:
            Clinical summary dictionary with risk level, summary, features, actions, alerts
        """
        # Format inputs for the prompt
        vitals_str = json.dumps(vitals, ensure_ascii=False)
        labs_str = json.dumps(labs, ensure_ascii=False)
        shap_str = json.dumps(shap_features, ensure_ascii=False)
        risk_str = json.dumps(prediction_risk, ensure_ascii=False)
        flags_str = (
            json.dumps(data_quality_flags, ensure_ascii=False)
            if data_quality_flags
            else "없음"
        )

        try:
            # Run the chain using LCEL
            result = self.chain.invoke(
                {
                    "patient_id": patient_id,
                    "vitals": vitals_str,
                    "labs": labs_str,
                    "shap_features": shap_str,
                    "prediction_risk": risk_str,
                    "data_quality_flags": flags_str,
                }
            )

            # Result is already parsed by PydanticOutputParser
            return {
                "patient_id": patient_id,
                "risk_level": result.risk_level,
                "risk_score": result.risk_score,
                "summary": result.summary,
                "key_features": result.key_features,
                "recommended_actions": result.recommended_actions,
                "data_quality_alerts": result.data_quality_alerts,
                "timestamp": None,  # Add server timestamp in API layer
            }
        except Exception as e:
            # Fallback response on error
            return {
                "patient_id": patient_id,
                "risk_level": "unknown",
                "risk_score": 0.0,
                "summary": f"요약 생성 중 오류 발생: {str(e)}",
                "key_features": [],
                "recommended_actions": ["수동으로 환자 데이터 확인 필요"],
                "data_quality_alerts": ["LLM 요약 생성 실패"],
                "error": str(e),
            }

    def generate_batch_summaries(
        self, patients: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate clinical summaries for multiple patients

        Args:
            patients: List of patient data dictionaries
                Each should contain: patient_id, vitals, labs, shap_features, prediction_risk

        Returns:
            List of clinical summary dictionaries
        """
        summaries = []
        for patient in patients:
            summary = self.generate_summary(
                patient_id=patient.get("patient_id", "unknown"),
                vitals=patient.get("vitals", {}),
                labs=patient.get("labs", {}),
                shap_features=patient.get("shap_features", []),
                prediction_risk=patient.get("prediction_risk", {}),
                data_quality_flags=patient.get("data_quality_flags"),
            )
            summaries.append(summary)
        return summaries


def create_clinical_summary_generator(
    llm_service: Optional[LLMService] = None,
) -> ClinicalSummaryGenerator:
    """
    Factory function to create ClinicalSummaryGenerator

    Args:
        llm_service: Optional LLMService instance

    Returns:
        ClinicalSummaryGenerator instance
    """
    return ClinicalSummaryGenerator(llm_service=llm_service)


if __name__ == "__main__":
    # Test clinical summary generation
    print("Testing Clinical Summary Generator...")

    generator = create_clinical_summary_generator()

    # Sample patient data
    sample_patient = {
        "patient_id": "demo_001",
        "vitals": {"map": 58, "sbp": 82, "hr": 120, "rr": 32, "spo2": 89},
        "labs": {"lactate": 4.2, "wbc": 18, "creatinine": 2.1},
        "shap_features": [
            {"feature": "map_mean", "value": 58, "contribution": -0.35},
            {"feature": "lactate_last", "value": 4.2, "contribution": 0.28},
            {"feature": "hr_max", "value": 120, "contribution": 0.15},
        ],
        "prediction_risk": {"mortality": 0.75, "pressor": 0.85, "vent": 0.45},
        "data_quality_flags": ["MAP 센서 간헐적 결측", "소변량 데이터 누락"],
    }

    summary = generator.generate_summary(**sample_patient)

    print("\n✅ Clinical Summary Generated:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
