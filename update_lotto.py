import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import time
from sqlalchemy import create_engine # 👈 [추가] DB 연결 도구

# --- 1. 설정 ---
COLUMN_NAMES = ['draw_no', 'date', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'bonus']

# --- 2. DB 접속 설정 (main.py와 100% 동일) ---
DB_USER = "lotto_user"
DB_PASS = "lotto_password"
DB_HOST = "192.168.1.90" # 👈 본인의 '시놀로지 NAS' IP
DB_PORT = "5433" # 👈 우리가 수정한 포트
DB_NAME = "lotto_db"

# (타입: str)
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# (타입: sqlalchemy.engine.Engine) - DB 연결 '엔진' 생성
try:
    engine = create_engine(DATABASE_URL)
    # DB 연결 테스트 (실패 시 즉시 중단)
    with engine.connect() as conn:
        print(f"✅ PostgreSQL DB ({DB_HOST}:{DB_PORT}) 연결 성공.")
except Exception as e:
    print(f"❌ DB 연결 실패: {e}")
    exit() # DB 연결 안 되면 스크립트 즉시 종료

# --- 3. (V13) 함수들 (100% 동일) ---
def get_latest_internet_draw_no() -> int | None:
    main_url = "https://dhlottery.co.kr/gameResult.do?method=byWin"
    try:
        response = requests.get(main_url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        h4_tag = soup.find("div", {"class": "win_result"}).find("h4")
        latest_no_str_with_char: str = h4_tag.find("strong").text
        latest_no_str: str = latest_no_str_with_char.replace("회", "")
        return int(latest_no_str)
    except Exception as e:
        print(f"❌ 오류: 인터넷 최신 회차 번호를 가져오는 데 실패했습니다: {e}")
        return None

def 긁어오기_함수(회차: int) -> list | None:
    url = f"https://dhlottery.co.kr/gameResult.do?method=byWin&drwNo={회차}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, "html.parser")
        win_result = soup.find("div", {"class": "win_result"})
        date_tag = soup.find("p", {"class": "desc"})
        
        if not win_result or not date_tag or '(년 월 일 추첨)' in date_tag.text:
            return None 
        
        date_text: str = date_tag.text.strip()
        추첨일: str = "" 
        if '년' in date_text: 
            clean_text = date_text.split('(')[1].split(')')[0].replace(' 추첨', '')
            추첨일 = clean_text.replace('년 ', '-').replace('월 ', '-').replace('일', '')
        elif '.' in date_text: 
            date_parts_paren = date_text.split('(')
            if len(date_parts_paren) < 2: return None
            date_parts_dot = date_parts_paren[1].split('.')
            if len(date_parts_dot) < 3: return None
            추첨일 = f"{date_parts_dot[0]}-{date_parts_dot[1]}-{date_parts_dot[2]}"
        else: 
            return None
        
        win_div = win_result.find("div", {"class": "num win"})
        bonus_div = win_result.find("div", {"class": "num bonus"}) 
        
        if win_div and bonus_div:
            win_balls_tags = win_div.find_all("span", {"class": "ball_645"})
            bonus_ball_tag = bonus_div.find("span", {"class": "ball_645"})
            
            if len(win_balls_tags) == 6 and bonus_ball_tag:
                당첨번호 = [int(ball.text) for ball in win_balls_tags]
                보너스번호 = int(bonus_ball_tag.text)
            else:
                return None
        else:
            return None
        
        return [회차] + [추첨일] + 당첨번호 + [보너스번호]
    except Exception:
        return None

# --- 메인 로직 시작 (V14 - DB 버전) ---
try:
    # --- 💡💡💡 'CSV 읽기'가 'DB 읽기'로 변경된 부분 💡💡💡 ---
    # (기존 V13) pd.read_csv(...)
    # (수정 V14) DB에서 'draw_no'의 최대값(max)을 1개만 가져옴
    sql_query = "SELECT MAX(draw_no) FROM lotto_draws"
    # (타입: pd.DataFrame)
    df_max_draw_no = pd.read_sql(sql_query, con=engine)
    
    # .iloc[0, 0] : 1행 1열의 값을 가져옴 (타입: int)
    csv_max_draw_no: int = int(df_max_draw_no.iloc[0, 0])
    # --- 💡💡💡 수정 완료 💡💡💡 ---
    
    print(f"현재 DB의 마지막 회차: {csv_max_draw_no}회 (테이블: lotto_draws)")

    internet_latest_draw_no: int | None = get_latest_internet_draw_no()
    if not internet_latest_draw_no:
        print("스크립트를 종료합니다.")
        exit()
    print(f"현재 인터넷의 최신 회차: {internet_latest_draw_no}회")

    새로_추가된_데이터 = [] # list
    
    if csv_max_draw_no < internet_latest_draw_no:
        print(f"DB가 최신이 아닙니다. {csv_max_draw_no + 1}회부터 {internet_latest_draw_no}회까지 업데이트를 시작합니다...")
        
        업데이트_할_회차 = csv_max_draw_no + 1
        while 업데이트_할_회차 <= internet_latest_draw_no:
            print(f" > {업데이트_할_회차}회차 당첨 번호를 웹에서 가져옵니다...")
            새_당첨번호_리스트 = 긁어오기_함수(업데이트_할_회차)
            
            if 새_당첨번호_리스트: # list
                새로_추가된_데이터.append(새_당첨번호_리스트)
                업데이트_할_회차 += 1
                time.sleep(0.5) 
            else: # None
                print(f" > {업데이트_할_회차}회차 긁어오기 실패. (원인은 함수 로그 확인) 루프를 중단합니다.")
                break 
    else:
        print(f"DB가 이미 인터넷과 동일한 최신 상태입니다. ({csv_max_draw_no}회)")
    
    # --- 💡💡💡 'CSV 저장'이 'DB 저장'으로 변경된 부분 💡💡💡 ---
    if 새로_추가된_데이터: 
        print(f"\n총 {len(새로_추가된_데이터)}건의 신규 데이터를 메모리에서 준비 중...")
        # (타입: pd.DataFrame)
        df_새데이터 = pd.DataFrame(새로_추가된_데이터, columns=COLUMN_NAMES)
        
        # (기존 V13) df_최신.to_csv(...)
        # (수정 V14) 'lotto_draws' 테이블에 'append'(추가) 모드로 저장
        print(f"'lotto_draws' 테이블에 {len(df_새데이터)}건을 'INSERT' 합니다...")
        df_새데이터.to_sql(
            'lotto_draws',
            con=engine,
            if_exists='append', # 👈 'replace'(덮어쓰기)가 아닌 'append'(추가)
            index=False       # 👈 pandas 인덱스(0,1,2..)는 저장 안 함
        )
        
        print(f"\n--- ✅ 총 {len(새로_추가된_데이터)}건의 새 당첨 정보를 'PostgreSQL DB'에 추가했습니다! ---")
    
    else: 
        print(f"\n--- ℹ️ 신규 추가 데이터 0건. DB 업데이트를 종료합니다. ---")
    # --- 💡💡💡 수정 완료 💡💡💡 ---

except Exception as e:
    print(f"❌ 스크립트 실행 중 치명적인 오류가 발생했습니다: {e}")