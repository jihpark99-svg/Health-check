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
DB_FILE = "health_analytics_v5.csv"

st.set_page_config(page_title="Pro Health Analyzer v5", layout="wide")

# CSS 스타일
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 12px; 
                box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e9ecef; }
    .advice-box { background-color: #f1fcf4; padding: 20px; border-radius: 10px; border-left: 5px solid #4caf50; margin-bottom: 20px; }
    .tip-header { font-size: 1.1rem; font-weight: bold; margin-bottom: 10px; }
    .delete-section { background-color: #fff5f5; padding: 15px; border-radius: 10px; border: 1px solid #feb2b2; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 로드 및 분석 함수
def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df[COL_DATE] = pd.to_datetime(df[COL_DATE]).dt.date
            return df
        except:
            pass
    return pd.DataFrame(columns=[COL_DATE, COL_NAME, COL_WEIGHT, COL_BMI, COL_BMR, COL_BFP, COL_BFP_CAT, COL_CALORIE])

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

# 3. 사이드바: 데이터 입력
with st.sidebar:
    st.header("👤 정보 입력")
    with st.form("input_form"):
        m_date = st.date_input("측정 일자", datetime.date.today())
        u_name = st.text_input("성명", placeholder="이름 입력")
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
    st.rerun()

# 4. 메인 화면
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

        st.divider()

        # 통합 그래프 섹션
        st.subheader(f"📈 {selected_user}님의 체중 및 BMI 통합 추이")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=user_df[COL_DATE], y=user_df[COL_WEIGHT], name="체중(kg)", mode='lines+markers', line=dict(color='blue', width=3)), secondary_y=False)
        fig.add_trace(go.Scatter(x=user_df[COL_DATE], y=user_df[COL_BMI], name="BMI", mode='lines+markers', line=dict(color='orange', width=3, dash='dot')), secondary_y=True)
        fig.update_layout(hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig.update_yaxes(title_text="체중 (kg)", secondary_y=False)
        fig.update_yaxes(title_text="BMI", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # 맞춤 조언 및 팁 (이미지 내용 반영)
        st.subheader("💡 맞춤 건강 조언")
        st.markdown("""
            <div class="advice-box">
                <p style="color:#2e7d32; font-weight:bold;">건강한 체중 유지 조언 ✅</p>
                <ul>
                    <li><b>영양:</b> 균형 잡힌 식단을 유지하세요 (채소, 단백질, 통곡물)</li>
                    <li><b>운동:</b> 주 150분 이상의 유산소 운동 + 주 2회 근력 운동</li>
                    <li><b>생활습관:</b> 충분한 수면(7-8시간)과 스트레스 관리</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

        # 5. 데이터 관리 (기록 삭제) 섹션
        with st.expander("🛠️ 데이터 관리 및 기록 삭제"):
            st.markdown('<div class="delete-section">', unsafe_allow_html=True)
            st.warning(f"선택된 사용자: **{selected_user}**")
            
            col_del1, col_del2 = st.columns(2)
            
            with col_del1:
                if st.button("🗑️ 최신 기록 1건 삭제"):
                    user_indices = df[df[COL_NAME] == selected_user].index
                    if not user_indices.empty:
                        df = df.drop(user_indices[-1])
                        df.to_csv(DB_FILE, index=False)
                        st.success("최신 기록이 삭제되었습니다.")
                        st.rerun()
            
            with col_del2:
                if st.button("🔥 사용자 모든 데이터 삭제"):
                    df = df[df[COL_NAME] != selected_user]
                    df.to_csv(DB_FILE, index=False)
                    st.success(f"{selected_user}님의 모든 기록이 삭제되었습니다.")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.write("---")
            st.dataframe(user_df.sort_values(COL_DATE, ascending=False), use_container_width=True)

    else:
        st.info("💡 사용자를 선택하면 분석 내용과 삭제 옵션이 나타납니다.")
else:
    st.info("기록된 데이터가 없습니다. 사이드바에서 정보를 입력해 주세요.")