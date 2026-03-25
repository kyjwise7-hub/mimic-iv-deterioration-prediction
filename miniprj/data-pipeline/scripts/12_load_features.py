import pandas as pd
import oracledb
import os
import time
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 설정
# ============================================================
CSV_PATH = '../data/processed/features_final_v2.csv'  # 경로 맞게 수정

DB_USER = os.getenv('ORACLE_USER')
DB_PASSWORD = os.getenv('ORACLE_PASSWORD')
DB_DSN = os.getenv('ORACLE_CONNECTION_STRING')

# ============================================================
# 헬퍼 함수
# ============================================================
def _fmt_hms(seconds: float) -> str:
    seconds = int(max(0, seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

# ============================================================
# CSV 로드
# ============================================================
print("CSV 로드 중...")
df = pd.read_csv(CSV_PATH)
print(f"  ✓ {len(df):,} rows 로드")

df.columns = df.columns.str.lower()
df = df.where(pd.notnull(df), None)

# ============================================================
# Oracle 연결
# ============================================================
print("Oracle 연결 중...")
oracledb.init_oracle_client(lib_dir="/opt/oracle/instantclient_23_3")
conn = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
cursor = conn.cursor()
print("  ✓ 연결 성공")

# ============================================================
# 데이터 적재
# ============================================================
print("데이터 적재 중...")

insert_sql = """
INSERT INTO features (
    stay_id, subject_id, hadm_id, observation_hour, observation_start, observation_end,
    hr, rr, spo2, sbp, dbp, mbp, temp, hr_max, rr_max, spo2_min, sbp_min,
    creatinine, wbc, platelets, potassium, sodium, lactate,
    gcs_eye, gcs_verbal, gcs_motor, gcs_total,
    urine_ml_6h, urine_ml_kg_hr_avg, oliguria_flag,
    shock_index, anchor_age, news_score, mews_score, lactate_missing, abga_checked, is_readmission,
    hr_delta, sbp_delta, spo2_delta, lactate_delta, gcs_total_delta,
    hr_slope, sbp_slope, spo2_slope, lactate_slope, gcs_total_slope,
    death_next_6h, vent_next_6h, pressor_next_6h, composite_next_6h,
    death_next_12h, vent_next_12h, pressor_next_12h, composite_next_12h,
    death_next_24h, vent_next_24h, pressor_next_24h, composite_next_24h
) VALUES (
    :stay_id, :subject_id, :hadm_id, :observation_hour,
    TO_TIMESTAMP(:observation_start, 'YYYY-MM-DD HH24:MI:SS'),
    TO_TIMESTAMP(:observation_end, 'YYYY-MM-DD HH24:MI:SS'),
    :hr, :rr, :spo2, :sbp, :dbp, :mbp, :temp, :hr_max, :rr_max, :spo2_min, :sbp_min,
    :creatinine, :wbc, :platelets, :potassium, :sodium, :lactate,
    :gcs_eye, :gcs_verbal, :gcs_motor, :gcs_total,
    :urine_ml_6h, :urine_ml_kg_hr_avg, :oliguria_flag,
    :shock_index, :anchor_age, :news_score, :mews_score, :lactate_missing, :abga_checked, :is_readmission,
    :hr_delta, :sbp_delta, :spo2_delta, :lactate_delta, :gcs_total_delta,
    :hr_slope, :sbp_slope, :spo2_slope, :lactate_slope, :gcs_total_slope,
    :death_next_6h, :vent_next_6h, :pressor_next_6h, :composite_next_6h,
    :death_next_12h, :vent_next_12h, :pressor_next_12h, :composite_next_12h,
    :death_next_24h, :vent_next_24h, :pressor_next_24h, :composite_next_24h
)
"""

batch_size = 5000  # 300만건이라 배치 사이즈 증가
total = len(df)

start_t = time.time()
last_t = start_t
last_done = 0

for i in range(0, total, batch_size):
    batch = df.iloc[i:i+batch_size].to_dict('records')
    cursor.executemany(insert_sql, batch)
    conn.commit()

    done = min(i + batch_size, total)
    pct = (done / total) * 100 if total else 100.0

    now = time.time()
    elapsed = now - start_t

    avg_rps = (done / elapsed) if elapsed > 0 else 0.0

    dt = now - last_t
    drows = done - last_done
    inst_rps = (drows / dt) if dt > 0 else 0.0

    remaining_rows = total - done
    eta_sec = (remaining_rows / avg_rps) if avg_rps > 0 else 0.0

    print(
        f"\r  {done:,}/{total:,} ({pct:6.2f}%) | "
        f"avg {avg_rps:,.0f} rows/s | "
        f"inst {inst_rps:,.0f} rows/s | "
        f"elapsed {_fmt_hms(elapsed)} | "
        f"ETA {_fmt_hms(eta_sec)}",
        end="",
        flush=True
    )

    last_t = now
    last_done = done

print(f"\n✓ 총 {total:,} rows 적재 완료")

cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN hr IS NULL THEN 1 ELSE 0 END) AS hr_null, SUM(CASE WHEN sbp IS NULL THEN 1 ELSE 0 END) AS sbp_null, SUM(CASE WHEN lactate IS NULL THEN 1 ELSE 0 END) AS lactate_null, SUM(CASE WHEN gcs_total IS NULL THEN 1 ELSE 0 END) AS gcs_null FROM features"); 
row = cursor.fetchone()
print(f"\n검증: total={row[0]:,}, hr_null={row[1]}, sbp_null={row[2]}, lactate_null={row[3]}, gcs_null={row[4]}")

# ============================================================
# 정리
# ============================================================
cursor.close()
conn.close()
print("✓ 연결 종료")