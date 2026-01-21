import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# 1. 상수 및 초기 설정
COL_DATE = "측정 일자"
COL_NAME = "성명"
COL_WEIGHT = "체중(kg)"
COL_BMI = "BMI 지수"
COL_BMR = "기초대사량(kcal)"
COL_BFP = "체지방률(%)"
COL_BFP_CAT = "체지방 범주"
COL_CALORIE = "권장칼로리(kcal)"
DB_FILE = "health_analytics_v5.csv" # 이 파일이 스크립트와 같은 폴더에 있어야 합니다.

st.set_page_config(page_title="Pro Health Analyzer v5", layout="wide")

# 2. 데이터 로드 함수 (자동 복구 로직 포함)
def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df[COL_DATE] = pd.to_datetime(df[COL_DATE]).dt.date
            return df
        except:
            st.error("CSV 파일을 읽는 중 오류가 발생했습니다. 파일 형식을 확인하세요.")
    # 파일이 없으면 빈 데이터프레임 생성
    return pd.DataFrame(columns=[COL_DATE, COL_NAME, COL_WEIGHT, COL_BMI, COL_BMR, COL_BFP, COL_BFP_CAT, COL_CALORIE])

# 3. 건강 분석 알고리즘
def get_analysis(weight, height, age, gender, activity):
    bmi = round(weight / ((height / 100) ** 2), 2)
    if gender == "남성":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        bfp = round((1.20 * bmi) + (0.23 * age) - 16.2, 1)
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
        bfp = round((1.20 * bmi) + (0.23 * age) - 5.4, 1)
    
    act_map = {"매우 적음": 1.2, "보통": 1.375, "활발함": 1.55, "매우 활발함": 1.725}
    kcal = int(bmr * act_map[activity])
    min_w = round(18.5 * ((height/100)**2), 1)
    max_w = round(23.0 * ((height/100)**2), 1)
    return bmi, int(bmr), bfp, kcal, min_w, max_w

df = load_data()

# --- 사이드바: 데이터 입력 및 전체 백업 ---
with st.sidebar:
    st.header("👤 정보 입력")
    with st.form("input_form"):
        m_date = st.date_input("측정 일자", datetime.date.today())
        u_name = st.text_input("성명")
        u_age = st.number_input("연령", 1, 100, 57)
        u_gen = st.radio("성별", ["남성", "여성"], horizontal=True)
        u_h = st.number_input("키 (cm)", 100.0, 250.0, 175.0)
        u_w = st.number_input("체중 (kg)", 30.0, 200.0, 70.0)
        u_a = st.selectbox("활동량", ["매우 적음", "보통", "활발함", "매우 활발함"])
        submit = st.form_submit_button("기록 저장")

    if submit and u_name.strip():
        bmi, bmr, bfp, kcal, _, _ = get_analysis(u_w, u_h, u_age, u_gen, u_a)
        new_row = {COL_DATE: m_date, COL_NAME: u_name, COL_WEIGHT: u_w, COL_BMI: bmi, 
                   COL_BMR: bmr, COL_BFP: bfp, COL_BFP_CAT: "분석완료", COL_CALORIE: kcal}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        st.success("데이터가 파일에 저장되었습니다!")
        st.rerun()

    st.divider()
    st.header("💾 전체 데이터 백업")
    if not df.empty:
        full_csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("내 컴퓨터로 CSV 백업하기", data=full_csv, file_name="health_backup.csv", mime="text/csv")

# --- 메인 화면 ---
st.title("🛡️ Smart Health Tracker Pro")

if not df.empty:
    user_list = sorted(df[COL_NAME].unique().tolist())
    selected_user = st.selectbox("🔍 사용자 선택", user_list, index=None, placeholder="성명을 선택하세요")
    
    if selected_user:
        user_df = df[df[COL_NAME] == selected_user].sort_values(COL_DATE)
        latest = user_df.iloc[-1]
        bmi, bmr, bfp, kcal, min_w, max_w = get_analysis(latest[COL_WEIGHT], u_h, u_age, u_gen, u_a)

        # 요약 지표 + 표준 범위
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("현재 체중", f"{latest[COL_WEIGHT]} kg")
            st.caption(f"📍 표준: {min_w} ~ {max_w} kg")
        with m2:
            st.metric("BMI 지수", f"{latest[COL_BMI]}")
            st.caption("📍 표준: 18.5 ~ 23.0")
        with m3:
            st.metric("기초대사량", f"{latest[COL_BMR]:,} kcal")
            st_bmr = "1,500~1,800" if u_gen == "남성" else "1,200~1,500"
            st.caption(f"📍 평균: 약 {st_bmr} kcal")
        with m4:
            st.metric("체지방률", f"{latest[COL_BFP]} %")
            st_bfp = "15~25%" if u_gen == "남성" else "20~32%"
            st.caption(f"📍 표준: {st_bfp}")

        # 통합 그래프 [보조축 사용]
        st.subheader("📈 통합 지표 변화 추이")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=user_df[COL_DATE], y=user_df[COL_WEIGHT], name="체중(kg)", mode='lines+markers'), secondary_y=False)
        fig.add_trace(go.Scatter(x=user_df[COL_DATE], y=user_df[COL_BMI], name="BMI", mode='lines+markers'), secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)

        # 삭제 및 관리 섹션
        with st.expander("🛠️ 데이터 관리 (기록 삭제)"):
            if st.button("🗑️ 최신 기록 삭제"):
                df = df.drop(df[df[COL_NAME] == selected_user].index[-1])
                df.to_csv(DB_FILE, index=False)
                st.rerun()
else:
    st.info("기록된 데이터가 없습니다. 사이드바에 정보를 입력하거나 기존 백업 파일을 확인하세요.")