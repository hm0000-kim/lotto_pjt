import requests
from bs4 import BeautifulSoup

# 1. 원하는 회차를 정합니다. (일단 1116회차로 테스트)
회차 = 1116
url = f"https://dhlottery.co.kr/gameResult.do?method=byWin&drwNo={회차}"

# 2. 'requests' (배달원)가 웹사이트에 접속해서 HTML 코드를 가져옵니다.
try:
    response = requests.get(url)
    response.raise_for_status() # 오류가 났는지 확인
    html = response.text
    
    # 3. 'BeautifulSoup' (요리사)가 HTML 코드를 분석하기 쉽게 정리합니다.
    soup = BeautifulSoup(html, "html.parser")
    
    # 4. 당첨 번호가 있는 태그(tag)를 찾습니다.
    # (개발자 도구로 미리 찾아본 결과, 'num win' 클래스에 번호가 있습니다)
    win_result = soup.find("div", {"class": "win_result"})
    
    if win_result:
        # 4-1. 6개의 당첨 번호 찾기
        win_balls = win_result.find_all("span", {"class": "ball_645"})
        당첨번호 = [ball.text for ball in win_balls]
        
        # 4-2. 보너스 번호 찾기
        bonus_ball = win_result.find("span", {"class": "bonu"})
        보너스번호 = bonus_ball.text if bonus_ball else "N/A"
        
        # 5. 결과를 출력합니다.
        print(f"--- {회차}회차 당첨 번호 ---")
        print(f"당첨 번호: {', '.join(당첨번호)}")
        print(f"보너스 번호: {보너스번호}")
    
    else:
        print(f"{회차}회차 당첨 정보를 찾을 수 없습니다.")

except requests.exceptions.RequestException as e:
    print(f"웹사이트 접속에 실패했습니다: {e}")
except Exception as e:
    print(f"알 수 없는 오류가 발생했습니다: {e}")