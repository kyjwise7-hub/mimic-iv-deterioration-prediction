CREATE TABLE simulation_state (
    id                  NUMBER(1) DEFAULT 1 NOT NULL,
    current_hour        NUMBER(5) DEFAULT 0 NOT NULL,
    status              VARCHAR2(20) DEFAULT 'STOPPED',
    last_updated        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT pk_simulation_state PRIMARY KEY (id),
    CONSTRAINT chk_single_row CHECK (id = 1)
);

INSERT INTO simulation_state (id, current_hour, status) VALUES (1, 0, 'STOPPED');
COMMIT;

-- Oracle에서 실행
UPDATE simulation_state SET current_hour = 24 WHERE id = 1;
COMMIT;


SELECT current_hour FROM simulation_state WHERE id = 1;

SELECT COUNT(*) FROM features WHERE observation_hour <= 24;

SELECT * FROM features WHERE stay_id = 30000153 AND observation_hour <= 24 FETCH FIRST 5 ROWS ONLY;



SELECT MAX(observation_hour) FROM features WHERE observation_hour <= 24;

SELECT COUNT(*) FROM features WHERE observation_hour = 24;

SELECT * FROM features WHERE observation_hour = 24 FETCH FIRST 10 ROWS ONLY;

SELECT 
  c.stay_id, c.subject_id, c.hadm_id, c.anchor_age, c.gender,
  c.first_careunit, c.intime,
  f.observation_hour, f.hr, f.rr, f.spo2, f.sbp, f.mbp, f.lactate,
  f.news_score, f.mews_score
FROM features f
JOIN cohort c ON c.stay_id = f.stay_id
WHERE f.observation_hour = 24
FETCH FIRST 100 ROWS ONLY;