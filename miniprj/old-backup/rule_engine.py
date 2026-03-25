"""
Rule-based Protocol Engine for MIMIC ICU Data

This module evaluates patient features against predefined clinical protocol rules
and generates action-oriented recommendations.
"""

import json
import os
from typing import Any, Dict, List, Optional


class RuleEngine:
    """Rule-based protocol evaluation engine"""

    def __init__(self, protocols_dir: str = "./protocols"):
        """
        Initialize the rule engine

        Args:
            protocols_dir: Directory containing protocol rule JSON files
        """
        self.protocols_dir = protocols_dir
        self.protocols = {}
        self._load_all_protocols()

    def _load_all_protocols(self):
        """Load all protocol rules from JSON files"""
        protocol_files = {
            "sepsis": "sepsis_rules.json",
            "vent": "vent_rules.json",
            "pressor": "pressor_rules.json",
        }

        for protocol_name, filename in protocol_files.items():
            filepath = os.path.join(self.protocols_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    self.protocols[protocol_name] = json.load(f)
            else:
                print(f"Warning: Protocol file not found: {filepath}")

    def _evaluate_condition(
        self, condition: Dict[str, Any], patient_features: Dict[str, Any]
    ) -> bool:
        """
        Evaluate a single condition against patient features

        Supported operators:
        - _ge: >=
        - _gt: >
        - _le: <=
        - _lt: <
        - _eq: ==
        - Boolean flags: on_oxygen, on_vent, on_pressor, on_hfnc

        Args:
            condition: Condition dictionary
            patient_features: Patient feature values

        Returns:
            True if condition is met, False otherwise
        """
        # Handle logical operators
        if "all" in condition:
            return all(
                self._evaluate_condition(c, patient_features) for c in condition["all"]
            )
        if "any" in condition:
            return any(
                self._evaluate_condition(c, patient_features) for c in condition["any"]
            )

        # Handle comparison operators
        for key, value in condition.items():
            # Extract feature name and operator
            if key.endswith("_ge"):
                feature = key[:-3]
                return patient_features.get(feature, float("inf")) >= value
            elif key.endswith("_gt"):
                feature = key[:-3]
                return patient_features.get(feature, float("inf")) > value
            elif key.endswith("_le"):
                feature = key[:-3]
                return patient_features.get(feature, float("-inf")) <= value
            elif key.endswith("_lt"):
                feature = key[:-3]
                return patient_features.get(feature, float("-inf")) < value
            elif key.endswith("_eq"):
                feature = key[:-3]
                return patient_features.get(feature) == value
            else:
                # Boolean flag (e.g., on_oxygen, on_vent)
                return patient_features.get(key, False) == value

        return False

    def evaluate_protocol(
        self, protocol_name: str, patient_features: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate a single protocol against patient features

        Args:
            protocol_name: Name of the protocol (sepsis, vent, pressor)
            patient_features: Patient feature dictionary

        Returns:
            List of triggered actions with metadata
        """
        if protocol_name not in self.protocols:
            return []

        protocol = self.protocols[protocol_name]
        triggered_actions = []

        for rule in protocol.get("rules", []):
            condition = rule.get("condition", {})
            if self._evaluate_condition(condition, patient_features):
                triggered_actions.append(
                    {
                        "rule_id": rule.get("rule_id"),
                        "protocol": protocol_name,
                        "priority": rule.get("priority", "MEDIUM"),
                        "action": rule.get("action"),
                        "evidence": rule.get("evidence", {}),
                    }
                )

        return triggered_actions

    def evaluate_all_protocols(
        self, patient_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate all protocols against patient features

        Args:
            patient_features: Patient feature dictionary

        Returns:
            Formatted output with active protocols and actions
        """
        all_actions = []

        # Evaluate each protocol
        for protocol_name in ["sepsis", "vent", "pressor"]:
            actions = self.evaluate_protocol(protocol_name, patient_features)
            all_actions.extend(actions)

        # Sort by priority (STAT > HIGH > MEDIUM)
        priority_order = {"STAT": 0, "HIGH": 1, "MEDIUM": 2}
        all_actions.sort(key=lambda x: priority_order.get(x["priority"], 3))

        # Determine active protocols
        active_protocols = list(set(action["protocol"] for action in all_actions))

        return {
            "patient_id": patient_features.get("patient_id", "unknown"),
            "active_protocols": active_protocols,
            "actions": all_actions,
        }

    def format_for_ui(self, evaluation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format evaluation result for UI consumption

        Args:
            evaluation_result: Result from evaluate_all_protocols

        Returns:
            UI-formatted result
        """
        # Group actions by protocol
        grouped_actions = {}
        for action in evaluation_result.get("actions", []):
            protocol = action["protocol"]
            if protocol not in grouped_actions:
                grouped_actions[protocol] = []
            grouped_actions[protocol].append(action)

        return {
            "patient_id": evaluation_result.get("patient_id"),
            "active_protocols": evaluation_result.get("active_protocols", []),
            "actions_by_protocol": grouped_actions,
            "total_actions": len(evaluation_result.get("actions", [])),
        }


def create_engine(protocols_dir: str = "./protocols") -> RuleEngine:
    """
    Factory function to create a RuleEngine instance

    Args:
        protocols_dir: Directory containing protocol rule JSON files

    Returns:
        Initialized RuleEngine instance
    """
    return RuleEngine(protocols_dir)


# Example usage
if __name__ == "__main__":
    # Sample patient data
    sample_patient = {
        "patient_id": "demo_001",
        "map": 58,
        "sbp": 82,
        "lactate": 4.2,
        "spo2": 89,
        "fio2": 0.5,
        "rr": 32,
        "on_oxygen": True,
        "on_hfnc": False,
        "on_vent": False,
        "on_pressor": False,
        "urine_output_ml_per_kg_hr": 0.3,
    }

    # Create engine and evaluate
    engine = create_engine()
    result = engine.evaluate_all_protocols(sample_patient)

    # Print results
    print(json.dumps(result, indent=2, ensure_ascii=False))
