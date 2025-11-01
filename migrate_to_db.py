import pandas as pd
import os
from sqlalchemy import create_engine # DB 연결 도구

# --- 1. DB 접속 정보 (docker-compose.yml과 동일) ---
DB_USER = "lotto_user"
DB_PASS = "lotto_password"

# --- 💡💡💡 여기가 수정된 부분입니다 💡💡💡 ---
# (기존) DB_HOST = "localhost" 
DB_HOST = "192.168.1.90" # 👈 본인의 '시놀로지 NAS' IP 주소를 입력하세요
# --- 💡💡💡 수정 완료 💡💡💡 ---

DB_PORT = "5433"
DB_NAME = "lotto_db"

# (이하 동일)
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- 2. CSV 파일 경로 (V13과 동일) ---
CSV_파일이름 = "winning_numbers.csv"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_절대경로 = os.path.join(BASE_DIR, CSV_파일이름)

try:
    # 3. CSV 읽기 (V13의 클리닝/정렬 로직 포함)
    print(f"'{CSV_절대경로}' 파일을 읽습니다...")
    df = pd.read_csv(CSV_절대경로, encoding='cp949', dtype={'draw_no': str})
    
    # (클리닝)
    df['date'] = df['date'].astype(str).str.slice(0, 10)
    # (정렬을 위해 타입 변환)
    df['draw_no'] = pd.to_numeric(df['draw_no'], errors='coerce')
    
    print(f"총 {len(df)}건의 데이터를 읽었습니다.")

    # 4. DB 엔진 생성 (델파이 TADOConnection.Connect)
    # (타입: sqlalchemy.engine.Engine)
    engine = create_engine(DATABASE_URL)
    
    print("PostgreSQL DB에 연결 중...")
    
    # 5. DB에 데이터 '밀어넣기' (가장 핵심!)
    # 'lotto_draws'라는 '테이블 이름'으로 저장
    # if_exists='replace': 만약 'lotto_draws' 테이블이 이미 있다면, 삭제하고 새로 만듦
    # index=False: pandas의 순번(0,1,2...)은 DB에 저장 안 함
    df.to_sql('lotto_draws', con=engine, if_exists='replace', index=False)
    
    print(f"--- ✅ 성공! {len(df)}건의 데이터를 'lotto_draws' 테이블에 이관(Migration)했습니다. ---")

except Exception as e:
    print(f"❌ 데이터 이관 중 오류가 발생했습니다: {e}")