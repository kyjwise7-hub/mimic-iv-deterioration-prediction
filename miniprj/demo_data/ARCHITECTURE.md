# Architecture: Demo Data Layer

## Overview
This project follows a 3-layer architecture to separate raw clinical data from the presented view used in the demo. This ensures the demo is fast, reliable, and tells a cohesive story without corrupting the raw data analysis pipeline.

## Layers

### 1. Raw Clinical Data Layer (Raw tables)
- **Purpose**: Precise replication of MIMIC-IV schema and content.
- **Tables**: `chartevents`, `labevents`, `inputevents`, `icustays`, etc.
- **Status**: Assumed to exist in the database (or mocked separately if needed).
- **Note**: Demo stories do NOT modify this layer directly.

### 2. Feature / Model Layer (Intermediate)
- **Purpose**: Computation of derived features and model risk scores.
- **Content**: Hourly aggregates, sliding window features, SHAP values.
- **Example**: `spo2_mean_6h`, `rr_slope_6h`.
- **Status**: Background processing layer (conceptual for the demo).

### 3. Presentation / Demo Layer (View)
- **Purpose**: "Single source of truth" for the UI Demo and NL2SQL.
- **Table**: `icu_current_status`
- **Characteristics**:
  - One row per patient (latest state).
  - Human-readable column names (e.g., `spo2_last` instead of `itemid=220277`).
  - Contains Pre-computed Risk Scores & RAG Triggers.
- **Data Source**: Populated from `demo_patients.sql` / `demo_patients.json`.

## Demo Files
- **`demo_patients.csv`**: Source of truth for the 6 patient stories.
- **`demo_patients.json`**: For Frontend UI mocking.
- **`demo_patients.sql`**: For Database/NL2SQL mocking (Oracle compatible).
