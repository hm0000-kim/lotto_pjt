import pandas as pd
import streamlit as st # streamlit을 'st'라는 별명으로 부릅니다.
import os
from collections import Counter

# --- 1. 설정 (V13, analyze.py와 동일) ---
CSV_파일이름 = "winning_numbers.csv"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_절대경로 = os.path.join(BASE_DIR, CSV_파일이름)

# --- 2. 데이터 로드 (pandas) ---
# @st.cache_data : 데이터를 캐시해서 1초만에 로드합니다. (Streamlit의 마법)
@st.cache_data
def load_data():
    if not os.path.exists(CSV_절대경로):
        return None
    df = pd.read_csv(CSV_절대경로, encoding='cp949', dtype={'draw_no': str})
    return df

df = load_data()

# --- 3. UI 그리기 (델파이 폼 디자인과 유사) ---

# st.title : 'TLabel'을 큰 글씨로 올립니다.
st.title("📊 나만의 로또 통계 대시보드")

if df is None:
    st.error("❌ 'winning_numbers.csv' 파일을 찾을 수 없습니다. 'update_lotto.py'를 먼저 실행하세요.")
else:
    # st.header : 'TLabel'을 중간 글씨로 올립니다.
    st.header(f"📈 총 {len(df)} 회차 데이터 분석")

    # st.dataframe : 'TDBGrid'를 올립니다. (CSV 데이터 전체 표시)
    st.dataframe(df)

    # st.subheader : 'TLabel'을 작은 글씨로 올립니다.
    st.subheader("🔢 당첨 번호 (보너스 제외) 빈도수 분석")

    # (analyze.py와 동일한 로직)
    number_columns = ['n1', 'n2', 'n3', 'n4', 'n5', 'n6']
    all_numbers_list = []
    for row in df[number_columns].values:
        valid_numbers = pd.to_numeric(row, errors='coerce')
        all_numbers_list.extend([int(n) for n in valid_numbers if pd.notna(n)])

    number_counts = Counter(all_numbers_list)

    # Counter 결과를 DataFrame으로 예쁘게 변환
    df_counts = pd.DataFrame(number_counts.items(), columns=['숫자', '출현 횟수'])
    df_counts = df_counts.sort_values(by='출현 횟수', ascending=False)

    # st.bar_chart : 'TChart' (막대 그래프)를 올립니다.
    st.bar_chart(df_counts.set_index('숫자'))

    # st.write : 'TMemo'처럼 텍스트를 씁니다.
    st.write("---")
    st.write("Top 10 (가장 많이 나온 수):", number_counts.most_common(10))
    st.write("Bottom 10 (가장 적게 나온 수):", number_counts.most_common()[:-11:-1])