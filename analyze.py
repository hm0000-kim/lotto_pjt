import pandas as pd
import os
from collections import Counter

# --- 1. 설정 ---
# V13 스크립트와 동일한 경로 설정 로직
CSV_파일이름 = "winning_numbers.csv"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_절대경로 = os.path.join(BASE_DIR, CSV_파일이름)
# ----------------------------------------------

try:
    # 1. CSV 파일 읽기 (V13과 동일한 '안전한' 읽기 방식)
    if not os.path.exists(CSV_절대경로):
        print(f"❌ 오류: '{CSV_절대경로}' 파일이 없습니다.")
        print("먼저 update_lotto.py를 실행하여 파일을 생성하세요.")
        exit()
        
    df = pd.read_csv(CSV_절대경로, encoding='cp949', dtype={'draw_no': str})
    
    if df.empty:
        print(f"❌ 오류: '{CSV_파일이름}' 파일이 비어있습니다.")
        exit()

    print(f"--- ✅ '({os.path.basename(CSV_절대경로)})' 파일 분석 시작 ---")
    print(f"총 {len(df)} 회차의 데이터를 분석합니다.\n")

    # 2. 통계 분석: 6개 당첨 번호 (n1 ~ n6) 컬럼만 선택
    # (보너스 번호는 통계에서 제외할 경우 'bonus'를 뺍니다. 포함할 경우 리스트에 추가)
    number_columns: list[str] = ['n1', 'n2', 'n3', 'n4', 'n5', 'n6']
    
    # 3. 모든 번호를 하나의 거대한 리스트로 합치기
    all_numbers_list = []
    
    # DataFrame을 순회하며 숫자들을 리스트에 추가
    # .values: DataFrame을 NumPy 배열로 변환하여 순회 속도를 높임
    for row in df[number_columns].values:
        # pd.to_numeric: 혹시 모를 비숫자(NaN) 값을 안전하게 변환
        valid_numbers = pd.to_numeric(row, errors='coerce')
        # NaN이 아닌 숫자(int)만 all_numbers_list에 추가
        all_numbers_list.extend([int(n) for n in valid_numbers if pd.notna(n)])

    # 4. 'Counter'를 사용하여 각 숫자의 출현 횟수를 계산
    # (델파이의 TDictionary<Integer, Integer>와 유사)
    number_counts = Counter(all_numbers_list)

    # 5. 가장 많이 나온 숫자 10개 (Top 10) 출력
    print("--- 📊 (보너스 제외) 가장 많이 나온 숫자 Top 10 ---")
    # number_counts.most_common(10) -> [(숫자, 횟수), ...]
    for i, (number, count) in enumerate(number_counts.most_common(10)):
        print(f"{i+1:2d}위.  공: {number:2d} (총 {count:3d} 회)") # :2d = 2칸 정렬

    # 6. (응용) 가장 적게 나온 숫자 10개 (Bottom 10) 출력
    print("\n--- 📊 (보너스 제외) 가장 적게 나온 숫자 Top 10 ---")
    # .most_common()[:-11:-1] -> 리스트의 맨 뒤에서 10개를 역순으로 가져옴
    for i, (number, count) in enumerate(number_counts.most_common()[:-11:-1]):
        print(f"{i+1:2d}위.  공: {number:2d} (총 {count:3d} 회)")

except Exception as e:
    print(f"❌ 스크립트 실행 중 치명적인 오류가 발생했습니다: {e}")