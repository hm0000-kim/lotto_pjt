import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import time

# --- 1. 설정 ---
CSV_파일이름 = "winning_numbers.csv"
COLUMN_NAMES = ['draw_no', 'date', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'bonus']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_절대경로 = os.path.join(BASE_DIR, CSV_파일이름)
# ----------------------------------------------

def get_latest_internet_draw_no() -> int | None:
    """ (V12와 동일) 인터넷 최신 회차 번호 (int) 반환 """
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
    """
    (V13) 'div.num.bonus' (s가 붙음) 구조로 파싱 로직을 통일합니다.
    """
    url = f"https://dhlottery.co.kr/gameResult.do?method=byWin&drwNo={회차}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, "html.parser")
        win_result = soup.find("div", {"class": "win_result"})
        date_tag = soup.find("p", {"class": "desc"})
        
        if not win_result or not date_tag or '(년 월 일 추첨)' in date_tag.text:
            print(f"  > [정보] {회차}회차: 미추첨 회차(태그 없음)로 판단. (None 반환)")
            return None 
        
        # (V9와 동일) 날짜 파싱 로직
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
            print(f"  > [오류] {회차}회차: 알 수 없는 날짜 형식: {date_text}")
            return None
        
        # --- 💡💡💡 'bonus' (s) 구조로 통일한 부분 (if/else 삭제) 💡💡💡 ---
        당첨번호: list[int] = []
        보너스번호: int = 0
        
        # 1. 'div.num.win'과 'div.num.bonus'를 찾습니다.
        win_div = win_result.find("div", {"class": "num win"})
        bonus_div = win_result.find("div", {"class": "num bonus"}) # (s가 붙은 'bonus'로 통일)
        
        # 2. 둘 다 찾았는지 확인 (1194, 1195 모두 이 로직을 타야 함)
        if win_div and bonus_div:
            win_balls_tags = win_div.find_all("span", {"class": "ball_645"})
            bonus_ball_tag = bonus_div.find("span", {"class": "ball_645"})
            
            if len(win_balls_tags) == 6 and bonus_ball_tag:
                당첨번호 = [int(ball.text) for ball in win_balls_tags]
                보너스번호 = int(bonus_ball_tag.text)
            else:
                print(f"  > [오류] {회차}회차: 번호/보너스 개수 불일치.")
                return None
        
        # 2. 둘 중 하나라도 못 찾았다면 (HTML 구조가 예상과 다르다면)
        else:
            print(f"  > [오류] {회차}회차: 'div.num.win' 또는 'div.num.bonus' 태그를 찾지 못했습니다.")
            return None
        # --- 💡💡💡 수정 완료 💡💡💡 ---
        
        return_data = [회차] + [추첨일] + 당첨번호 + [보너스번호] # list
        return return_data
        
    except Exception as e:
        print(f"  > [오류] 데이터 파싱 오류 (회차: {회차}): {e}")
        raise e # 강제 중단

# --- 메인 로직 시작 (V12와 동일) ---
try:
    if not os.path.exists(CSV_절대경로):
        print(f"❌ 오류: '{CSV_절대경로}' 파일이 없습니다.")
        exit()
    df_기존 = pd.read_csv(CSV_절대경로, encoding='cp949', dtype={'draw_no': str})
    df_기존['date'] = df_기존['date'].astype(str).str.slice(0, 10)
    numeric_draw_no = pd.to_numeric(df_기존['draw_no'], errors='coerce')
    csv_max_draw_no: int = 0
    if not numeric_draw_no.isnull().all():
        csv_max_draw_no = int(numeric_draw_no.max()) 
    print(f"현재 CSV의 마지막 회차: {csv_max_draw_no}회 (파일: {CSV_절대경로})")
    internet_latest_draw_no: int | None = get_latest_internet_draw_no()
    if not internet_latest_draw_no:
        print("스크립트를 종료합니다.")
        exit()
    print(f"현재 인터넷의 최신 회차: {internet_latest_draw_no}회")

    새로_추가된_데이터 = [] # list
    
    if csv_max_draw_no < internet_latest_draw_no:
        print(f"CSV가 최신이 아닙니다. {csv_max_draw_no + 1}회부터 {internet_latest_draw_no}회까지 업데이트를 시작합니다...")
        
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
        print(f"CSV가 이미 인터넷과 동일한 최신 상태입니다. ({csv_max_draw_no}회)")
    
    # (V12와 동일) 저장/정렬 로직
    if 새로_추가된_데이터: 
        print(f"\n총 {len(새로_추가된_데이터)}건의 신규 데이터를 메모리에서 준비 중...")
        df_새데이터 = pd.DataFrame(새로_추가된_데이터, columns=COLUMN_NAMES)
        df_새데이터['draw_no'] = df_새데이터['draw_no'].astype(str)
        df_최신 = pd.concat([df_기존, df_새데이터], ignore_index=True)
    else: 
        print(f"\n신규 추가 데이터 0건. (클리닝 및 정렬 작업만 수행)")
        df_최신 = df_기존.copy() 
    print(f"[정보] {len(df_최신)}개 전체 데이터를 'draw_no' (회차) 기준으로 내림차순 정렬합니다...")
    df_최신['draw_no'] = pd.to_numeric(df_최신['draw_no'], errors='coerce')
    df_최신 = df_최신.sort_values(by='draw_no', ascending=False, na_position='last')
    print(f"'{CSV_절대경로}' 파일에 (내림차순 정렬하여) 저장(덮어쓰기)을 시도합니다...")
    df_최신.to_csv(CSV_절대경로, index=False, encoding='cp949')
    if 새로_추가된_데이터:
        print(f"\n--- ✅ 총 {len(새로_추가된_데이터)}건의 새 당첨 정보를 '{CSV_절대경로}'에 추가했습니다! ---")
    else:
        print(f"\n--- ✅ 데이터 클리닝 및 정렬 작업이 완료되었습니다. ---")

except Exception as e:
    print(f"❌ 스크립트 실행 중 치명적인 오류가 발생했습니다: {e}")