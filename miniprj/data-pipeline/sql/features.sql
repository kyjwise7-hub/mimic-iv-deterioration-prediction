DROP TABLE features;

CREATE TABLE features (
    -- 식별자
    stay_id             NUMBER(10)      NOT NULL,
    subject_id          NUMBER(10)      NOT NULL,
    hadm_id             NUMBER(10)      NOT NULL,
    observation_hour    NUMBER(5)       NOT NULL,
    observation_start   TIMESTAMP,
    observation_end     TIMESTAMP,
    
    -- 활력징후
    hr                  NUMBER,
    rr                  NUMBER,
    spo2                NUMBER,
    sbp                 NUMBER,
    dbp                 NUMBER,
    mbp                 NUMBER,
    temp                NUMBER,
    hr_max              NUMBER,
    rr_max              NUMBER,
    spo2_min            NUMBER,
    sbp_min             NUMBER,
    
    -- 검사
    creatinine          NUMBER,
    wbc                 NUMBER,
    platelets           NUMBER,
    potassium           NUMBER,
    sodium              NUMBER,
    lactate             NUMBER,
    
    -- GCS
    gcs_eye             NUMBER,
    gcs_verbal          NUMBER,
    gcs_motor           NUMBER,
    gcs_total           NUMBER,
    
    -- 소변량
    urine_ml_6h         NUMBER,
    urine_ml_kg_hr_avg  NUMBER,
    oliguria_flag       NUMBER,
    
    -- 파생지표
    shock_index         NUMBER,
    anchor_age          NUMBER,
    news_score          NUMBER,
    mews_score          NUMBER,
    lactate_missing     NUMBER,
    abga_checked        NUMBER,
    is_readmission      NUMBER,
    
    -- 트렌드 (delta)
    hr_delta            NUMBER,
    sbp_delta           NUMBER,
    spo2_delta          NUMBER,
    lactate_delta       NUMBER,
    gcs_total_delta     NUMBER,
    
    -- 트렌드 (slope)
    hr_slope            NUMBER,
    sbp_slope           NUMBER,
    spo2_slope          NUMBER,
    lactate_slope       NUMBER,
    gcs_total_slope     NUMBER,
    
    -- 타겟 (6h)
    death_next_6h       NUMBER,
    vent_next_6h        NUMBER,
    pressor_next_6h     NUMBER,
    composite_next_6h   NUMBER,
    
    -- 타겟 (12h)
    death_next_12h      NUMBER,
    vent_next_12h       NUMBER,
    pressor_next_12h    NUMBER,
    composite_next_12h  NUMBER,
    
    -- 타겟 (24h)
    death_next_24h      NUMBER,
    vent_next_24h       NUMBER,
    pressor_next_24h    NUMBER,
    composite_next_24h  NUMBER,
    
    CONSTRAINT pk_features PRIMARY KEY (stay_id, observation_hour),
    CONSTRAINT fk_features_cohort FOREIGN KEY (stay_id) REFERENCES cohort(stay_id)
);

CREATE INDEX idx_features_hour ON features(observation_hour);


SELECT tablespace_name, ROUND(SUM(bytes)/1024/1024, 2) AS used_mb FROM user_segments GROUP BY tablespace_name;