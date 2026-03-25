"""
Q&A Interface Module

This module converts natural language queries into patient filter parameters using LangChain.
"""

import json
from typing import Any, Dict, Optional

from llm_service import LLMService, create_llm_service


class QAInterface:
    """Convert natural language queries to patient filters"""

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize Q&A interface

        Args:
            llm_service: LLMService instance (creates new one if not provided)
        """
        self.llm_service = llm_service or create_llm_service()
        self.chain = self.llm_service.create_qa_filter_chain()

    def parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parse natural language query into filter parameters

        Args:
            query: Natural language query (e.g., "최근 2시간 내 위험도 급상승한 환자 보여줘")

        Returns:
            Dictionary with filters, interpretation, and sort_by
        """
        if not query or not query.strip():
            return {
                "filters": {},
                "interpretation": "질의가 비어있습니다.",
                "sort_by": None,
                "error": "Empty query",
            }

        try:
            # Run the chain using LCEL
            result = self.chain.invoke({"query": query.strip()})

            # Result is already parsed by PydanticOutputParser
            return {
                "filters": result.filters,
                "interpretation": result.interpretation,
                "sort_by": result.sort_by,
                "original_query": query,
            }
        except Exception as e:
            # Fallback response on error
            return {
                "filters": {},
                "interpretation": f"질의 파싱 중 오류 발생: {str(e)}",
                "sort_by": None,
                "original_query": query,
                "error": str(e),
            }

    def apply_filters(
        self, patients: list[Dict[str, Any]], filters: Dict[str, Any]
    ) -> list[Dict[str, Any]]:
        """
        Apply filters to patient list (simple implementation)

        Args:
            patients: List of patient dictionaries
            filters: Filter parameters from parse_query

        Returns:
            Filtered patient list
        """
        filtered = patients

        # Apply risk_type filter
        if "risk_type" in filters:
            risk_type = filters["risk_type"]
            filtered = [
                p
                for p in filtered
                if p.get("prediction_risk", {}).get(risk_type, 0) > 0
            ]

        # Apply risk_level filter
        if "risk_level" in filters:
            risk_level = filters["risk_level"]
            threshold_map = {"high": 0.7, "medium": 0.4, "low": 0}

            threshold = threshold_map.get(risk_level, 0)
            risk_type = filters.get("risk_type", "mortality")

            filtered = [
                p
                for p in filtered
                if p.get("prediction_risk", {}).get(risk_type, 0) >= threshold
            ]

        # Apply top_n filter
        if "top_n" in filters:
            top_n = int(filters["top_n"])
            risk_type = filters.get("risk_type", "mortality")

            # Sort by risk type and take top N
            filtered = sorted(
                filtered,
                key=lambda p: p.get("prediction_risk", {}).get(risk_type, 0),
                reverse=True,
            )[:top_n]

        return filtered

    def query_patients(
        self, query: str, patients: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        End-to-end query processing: parse query and filter patients

        Args:
            query: Natural language query
            patients: List of patient dictionaries

        Returns:
            Dictionary with parsed query, filtered patients, and metadata
        """
        parsed = self.parse_query(query)

        if "error" in parsed:
            return {
                "query": query,
                "parsed": parsed,
                "patients": [],
                "count": 0,
            }

        filters = parsed.get("filters", {})
        filtered_patients = self.apply_filters(patients, filters)

        # Apply sorting if specified
        sort_by = parsed.get("sort_by")
        if sort_by:
            # Simple sort logic (can be extended)
            if "risk" in sort_by:
                risk_type = sort_by.replace("_risk", "")
                filtered_patients = sorted(
                    filtered_patients,
                    key=lambda p: p.get("prediction_risk", {}).get(risk_type, 0),
                    reverse=True,
                )

        return {
            "query": query,
            "parsed": parsed,
            "patients": filtered_patients,
            "count": len(filtered_patients),
        }


def create_qa_interface(llm_service: Optional[LLMService] = None) -> QAInterface:
    """
    Factory function to create QAInterface

    Args:
        llm_service: Optional LLMService instance

    Returns:
        QAInterface instance
    """
    return QAInterface(llm_service=llm_service)


if __name__ == "__main__":
    # Test Q&A interface
    print("Testing Q&A Interface...")

    qa = create_qa_interface()

    # Test queries
    test_queries = [
        "최근 2시간 내 위험도 급상승한 환자 보여줘",
        "Pressor 위험 상위 5명",
        "사망 위험 높은 환자",
        "Vent 시작 가능성 중간 이상인 환자",
    ]

    for query in test_queries:
        print(f"\n질의: {query}")
        result = qa.parse_query(query)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    # Test with sample patients
    print("\n\n=== Testing with sample patients ===")
    sample_patients = [
        {
            "patient_id": "P001",
            "prediction_risk": {"mortality": 0.85, "pressor": 0.75, "vent": 0.45},
        },
        {
            "patient_id": "P002",
            "prediction_risk": {"mortality": 0.35, "pressor": 0.90, "vent": 0.20},
        },
        {
            "patient_id": "P003",
            "prediction_risk": {"mortality": 0.65, "pressor": 0.40, "vent": 0.80},
        },
    ]

    result = qa.query_patients("Pressor 위험 상위 2명", sample_patients)
    print("\n질의 결과:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
