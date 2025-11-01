import requests
from bs4 import BeautifulSoup

# --- 1. 진단할 회차 (문제가 된 1194회차) ---
회차: int = 1195
url: str = f"https://dhlottery.co.kr/gameResult.do?method=byWin&drwNo={회차}"

print(f"--- {회차}회차 HTML 구조 진단 시작 ---")
print(f"URL: {url}\n")

try:
    response = requests.get(url, timeout=5)
    response.raise_for_status() 
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 번호가 포함된 전체 영역('div.win_result')을 찾습니다.
    win_result = soup.find("div", {"class": "win_result"})
    
    if win_result:
        print("--- 'div.win_result' 영역의 HTML ---")
        # 찾은 영역의 HTML을 '예쁘게' 출력합니다.
        print(win_result.prettify())
        print("---------------------------------")
    else:
        print(f"❌ 오류: {회차}회차 페이지에서 'div.win_result' 영역을 찾지 못했습니다.")

except Exception as e:
    print(f"❌ 오류: {회차}회차 접속 또는 파싱에 실패했습니다: {e}")