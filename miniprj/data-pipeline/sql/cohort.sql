DROP TABLE D_HCPCS;
DROP TABLE D_HCPCS_TEAM4;

CREATE TABLE cohort (
    stay_id NUMBER PRIMARY KEY,
    subject_id NUMBER NOT NULL,
    hadm_id NUMBER NOT NULL,
    intime TIMESTAMP,
    outtime TIMESTAMP,
    los NUMBER,
    first_careunit VARCHAR2(100),
    last_careunit VARCHAR2(100),
    anchor_age NUMBER,
    gender VARCHAR2(10),
    dod DATE,
    admittime TIMESTAMP,
    dischtime TIMESTAMP,
    deathtime TIMESTAMP,
    hospital_expire_flag NUMBER(1),
    icu_seq NUMBER,
    is_readmission NUMBER(1),
    icu_mortality NUMBER(1),
    hospital_mortality NUMBER(1),
    dnr_time TIMESTAMP,
    vent_start_time TIMESTAMP,
    pressor_start_time TIMESTAMP
);


CREATE INDEX idx_cohort_subject ON cohort(subject_id);
CREATE INDEX idx_cohort_hadm ON cohort(hadm_id);


SELECT * FROM COHORT;


CREATE INDEX idx_features_hour_stay ON features(observation_hour, stay_id);

CREATE INDEX idx_cohort_stay_id ON cohort(stay_id);

EXPLAIN PLAN FOR
SELECT 
  c.stay_id, c.subject_id, c.hadm_id, c.anchor_age, c.gender,
  c.first_careunit, c.intime,
  f.observation_hour, f.hr, f.rr, f.spo2, f.sbp, f.mbp, f.lactate,
  f.news_score, f.mews_score
FROM features f
JOIN cohort c ON c.stay_id = f.stay_id
WHERE f.observation_hour = 24
FETCH FIRST 100 ROWS ONLY;

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);

SELECT /*+ LEADING(f) USE_NL(c) */
  c.stay_id, c.subject_id, c.hadm_id, c.anchor_age, c.gender,
  c.first_careunit, c.intime,
  f.observation_hour, f.hr, f.rr, f.spo2, f.sbp, f.mbp, f.lactate,
  f.news_score, f.mews_score
FROM features f
JOIN cohort c ON c.stay_id = f.stay_id
WHERE f.observation_hour = 24
FETCH FIRST 100 ROWS ONLY;