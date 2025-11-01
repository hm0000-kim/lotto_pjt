import pandas as pd
import os
from collections import Counter
from fastapi import FastAPI
from sqlalchemy import create_engine # 👈 [추가] DB 연결 도구

# --- 1. FastAPI 앱 생성 ---
app: FastAPI = FastAPI()


# --- 2. DB 접속 설정 (migrate_to_db.py와 100% 동일) ---
DB_USER = "lotto_user"
DB_PASS = "lotto_password"
DB_HOST = "192.168.1.90" # 👈 본인의 '시놀로지 NAS' IP
DB_PORT = "5433" # 👈 우리가 수정한 포트
DB_NAME = "lotto_db"

# (타입: str)
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# (타입: sqlalchemy.engine.Engine) - DB 연결 '엔진' 생성
engine = create_engine(DATABASE_URL)


# --- 3. 통계 분석 함수 (DB에서 읽도록 수정) ---
def load_and_analyze_data() -> dict:
    """
    (V3) CSV 대신, PostgreSQL DB에서 데이터를 읽어옵니다.
    """
    try:
        # --- 💡💡💡 'CSV 읽기'가 'DB 읽기'로 변경된 부분 💡💡💡 ---
        # (기존 V2) df: pd.DataFrame = pd.read_csv(CSV_절대경로, ...)
        
        # (수정 V3) DB의 'lotto_draws' 테이블 전체를 DataFrame으로 읽어옴
        # (타입: pd.DataFrame)
        df: pd.DataFrame = pd.read_sql("SELECT * FROM lotto_draws", con=engine)
        # --- 💡💡💡 수정 완료 💡💡💡 ---
        
        if df.empty:
            return {"error": "'lotto_draws' 테이블이 비어있습니다."}

        # (이하는 analyze.py, main.py V2와 100% 동일한 로직)
        # (Pandas의 위대한 점: 데이터 소스가 CSV든 DB든, 'df'로 동일하게 처리)
        number_columns: list[str] = ['n1', 'n2', 'n3', 'n4', 'n5', 'n6']
        all_numbers_list: list[int] = []
        for row in df[number_columns].values:
            valid_numbers = pd.to_numeric(row, errors='coerce')
            all_numbers_list.extend([int(n) for n in valid_numbers if pd.notna(n)])
        
        number_counts = Counter(all_numbers_list)
        top_10 = number_counts.most_common(10)
        bottom_10 = number_counts.most_common()[:-11:-1]
        
        return {
            "total_draws_analyzed": len(df),
            "total_numbers_counted": len(all_numbers_list),
            "top_10_most_common": top_10,
            "bottom_10_least_common": bottom_10
        }
    except Exception as e:
        # (DB 연결 오류 등도 여기서 잡힘)
        return {"error": f"DB 접속 또는 데이터 분석 중 오류 발생: {e}"}


# --- 4. API 엔드포인트(URL) 정의 (V2와 100% 동일) ---

@app.get("/")
def read_root() -> dict:
    return {"message": "로또 API 서버가 정상 작동 중입니다. (V3 - DB 연결 완료)"}


@app.get("/api/stats")
def get_stats() -> dict:
    stats_data = load_and_analyze_data()
    return stats_data