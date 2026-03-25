#!/usr/bin/env python3
"""
Simple test script for rule engine without Flask dependencies
"""

import json
from rule_engine import create_engine


def test_septic_shock_case():
    """Test Case 1: Septic shock (low MAP, high lactate)"""
    print("=" * 60)
    print("Test Case 1: Septic Shock")
    print("=" * 60)
    
    patient = {
        "patient_id": "case_001_septic_shock",
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
    
    engine = create_engine()
    result = engine.evaluate_all_protocols(patient)
    
    print(f"\nPatient ID: {result['patient_id']}")
    print(f"Active Protocols: {', '.join(result['active_protocols'])}")
    print(f"\nTotal Actions: {len(result['actions'])}\n")
    
    for i, action in enumerate(result['actions'], 1):
        print(f"{i}. [{action['priority']}] {action['action']}")
        print(f"   Protocol: {action['protocol']}")
        print(f"   Evidence: {action['evidence']['source']}, p.{action['evidence']['page']}")
        print()


def test_respiratory_failure_case():
    """Test Case 2: Respiratory failure (low SpO2, high RR)"""
    print("=" * 60)
    print("Test Case 2: Respiratory Failure")
    print("=" * 60)
    
    patient = {
        "patient_id": "case_002_respiratory_failure",
        "map": 75,
        "sbp": 110,
        "lactate": 1.5,
        "spo2": 87,
        "fio2": 0.7,
        "rr": 34,
        "on_oxygen": True,
        "on_hfnc": True,
        "on_vent": False,
        "on_pressor": False,
        "urine_output_ml_per_kg_hr": 0.8,
    }
    
    engine = create_engine()
    result = engine.evaluate_all_protocols(patient)
    
    print(f"\nPatient ID: {result['patient_id']}")
    print(f"Active Protocols: {', '.join(result['active_protocols'])}")
    print(f"\nTotal Actions: {len(result['actions'])}\n")
    
    for i, action in enumerate(result['actions'], 1):
        print(f"{i}. [{action['priority']}] {action['action']}")
        print(f"   Protocol: {action['protocol']}")
        print(f"   Evidence: {action['evidence']['source']}, p.{action['evidence']['page']}")
        print()


def test_stable_patient_case():
    """Test Case 3: Relatively stable patient"""
    print("=" * 60)
    print("Test Case 3: Stable Patient")
    print("=" * 60)
    
    patient = {
        "patient_id": "case_003_stable",
        "map": 75,
        "sbp": 120,
        "lactate": 1.2,
        "spo2": 96,
        "fio2": 0.21,
        "rr": 18,
        "on_oxygen": False,
        "on_hfnc": False,
        "on_vent": False,
        "on_pressor": False,
        "urine_output_ml_per_kg_hr": 1.2,
    }
    
    engine = create_engine()
    result = engine.evaluate_all_protocols(patient)
    
    print(f"\nPatient ID: {result['patient_id']}")
    print(f"Active Protocols: {', '.join(result['active_protocols'])}")
    print(f"\nTotal Actions: {len(result['actions'])}\n")
    
    if result['actions']:
        for i, action in enumerate(result['actions'], 1):
            print(f"{i}. [{action['priority']}] {action['action']}")
            print(f"   Protocol: {action['protocol']}")
            print(f"   Evidence: {action['evidence']['source']}, p.{action['evidence']['page']}")
            print()
    else:
        print("No active protocols - patient is stable! ✓\n")


def test_complex_case():
    """Test Case 4: Complex multi-system failure"""
    print("=" * 60)
    print("Test Case 4: Multi-System Failure")
    print("=" * 60)
    
    patient = {
        "patient_id": "case_004_complex",
        "map": 52,
        "sbp": 78,
        "lactate": 5.8,
        "spo2": 85,
        "fio2": 0.8,
        "rr": 36,
        "on_oxygen": True,
        "on_hfnc": True,
        "on_vent": False,
        "on_pressor": False,
        "urine_output_ml_per_kg_hr": 0.2,
    }
    
    engine = create_engine()
    result = engine.evaluate_all_protocols(patient)
    
    print(f"\nPatient ID: {result['patient_id']}")
    print(f"Active Protocols: {', '.join(result['active_protocols'])}")
    print(f"\nTotal Actions: {len(result['actions'])}\n")
    
    # Group by priority
    stat_actions = [a for a in result['actions'] if a['priority'] == 'STAT']
    high_actions = [a for a in result['actions'] if a['priority'] == 'HIGH']
    
    if stat_actions:
        print(f"🚨 STAT Actions ({len(stat_actions)}):")
        for i, action in enumerate(stat_actions, 1):
            print(f"  {i}. {action['action']}")
        print()
    
    if high_actions:
        print(f"⚠️  HIGH Priority Actions ({len(high_actions)}):")
        for i, action in enumerate(high_actions, 1):
            print(f"  {i}. {action['action']}")
        print()


if __name__ == "__main__":
    test_septic_shock_case()
    test_respiratory_failure_case()
    test_stable_patient_case()
    test_complex_case()
    
    print("=" * 60)
    print("All tests completed successfully! ✓")
    print("=" * 60)
