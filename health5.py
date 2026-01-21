import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
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

# CSS: 전문적인 대시보드 및 조언 박스 스타일
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 12px; 
                box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e9ecef; }
    .advice-box { background-color: #f1fcf4; padding: 20px; border-radius: 10px; border-left: 5px solid #4caf50; margin-bottom: 20px; }
    .tip-header { font-size: 1.1rem; font-weight: bold; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 로드 함수
def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df[COL_DATE] = pd.to_datetime(df[COL_DATE]).dt.date
            return df.sort_values(COL_DATE)
        except:
            pass
    return pd.DataFrame(columns=[COL_DATE, COL_NAME, COL_WEIGHT, COL_BMI, COL_BMR, COL_BFP, COL_BFP_CAT, COL_CALORIE])

# 3. 건강 분석 알고리즘
def get_analysis(weight, height, age, gender, activity):
    bmi = round(weight / ((height / 100) ** 2), 2)
    if gender == "남성":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        bfp = round((1.20 * bmi) + (0.23 * age) - 16.2, 1)
        bfp_cat = "비만" if bfp >= 25 else "정상/관리"
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
        bfp = round((1.20 * bmi) + (0.23 * age) - 5.4, 1)
        bfp_cat = "비만" if bfp >= 32 else "정상/관리"
    
    act_map = {"매우 적음": 1.2, "보통": 1.375, "활발함": 1.55, "매우 활발함": 1.725}
    kcal = int(bmr * act_map[activity])
    min_w = round(18.5 * ((height/100)**2), 1)
    max_w = round(23.0 * ((height/100)**2), 1)
    
    return bmi, int(bmr), bfp, bfp_cat, kcal, min_w, max_w

# --- 데이터 준비 ---
df = load_data()

# --- 사이드바: 입력 인터페이스 ---
with st.sidebar:
    st.header("👤 정보 입력")
    with st.form("input_form"):
        m_date = st.date_input("측정 일자", datetime.date.today())
        u_name = st.text_input("성명", placeholder="이름을 입력하세요")
        u_age = st.number_input("연령", 1, 100, 57)
        u_gen = st.radio("성별", ["남성", "여성"], horizontal=True)
        u_h = st.number_input("키 (cm)", 100.0, 250.0, 175.0)
        u_w = st.number_input("체중 (kg)", 30.0, 200.0, 70.0)
        u_a = st.selectbox("활동량", ["매우 적음", "보통", "활발함", "매우 활발함"])
        submit = st.form_submit_button("기록 저장")

if submit and u_name.strip():
    if len(u_name.strip()) < 2:
        st.sidebar.error("이름을 2자 이상 정확히 입력해주세요.")
    else:
        bmi, bmr, bfp, bfp_cat, kcal, _, _ = get_analysis(u_w, u_h, u_age, u_gen, u_a)
        new_row = {COL_DATE: m_date, COL_NAME: u_name, COL_WEIGHT: u_w, COL_BMI: bmi, 
                   COL_BMR: bmr, COL_BFP: bfp, COL_BFP_CAT: bfp_cat, COL_CALORIE: kcal}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        st.rerun()

# --- 메인 대시보드 ---
st.title("🛡️ Smart Health Tracker Pro")

if not df.empty:
    user_list = sorted(df[COL_NAME].unique().tolist())
    selected_user = st.selectbox("🔍 사용자 선택", user_list, index=None, placeholder="건강 정보를 확인할 성명을 선택하세요")
    
    if selected_user:
        user_df = df[df[COL_NAME] == selected_user].sort_values(COL_DATE)
        latest = user_df.iloc[-1]
        
        # 최신 정보 기준 분석 재산출
        bmi, bmr, bfp, bfp_cat, kcal, min_w, max_w = get_analysis(latest[COL_WEIGHT], u_h, u_age, u_gen, u_a)

        # 1. 요약 지표 및 표준 범위 표시
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

        # 2. 맞춤 건강 조언 (이미지 내용 반영)
        st.subheader("💡 맞춤 건강 조언")
        st.markdown(f"""
            <div class="advice-box">
                <p style="color:#2e7d32; font-weight:bold;">건강한 체중 유지 조언 ✅</p>
                <ul>
                    <li><b>영양:</b> 균형 잡힌 식단을 유지하세요 (채소, 단백질, 통곡물)</li>
                    <li><b>운동:</b> 주 150분 이상의 유산소 운동 + 주 2회 근력 운동</li>
                    <li><b>생활습관:</b> 충분한 수면(7~8시간)과 스트레스 관리</li>
                    <li><b>정기검진:</b> 연 1회 건강검진으로 건강 상태 확인</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

        # 3. 실천 가능한 건강 팁
        st.subheader("🥗 실천 가능한 건강 팁")
        col_diet, col_exercise = st.columns(2)
        with col_diet:
            st.markdown("""
                <div class="tip-header">식습관 개선 🍽️</div>
                <ul style="font-size:0.95rem; line-height:1.7;">
                    <li>아침 식사를 거르지 마세요</li>
                    <li>식사 시 천천히 씹어 먹으세요 (20분 이상)</li>
                    <li>물을 충분히 마시세요 (하루 2L 이상)</li>
                    <li>야식과 간식을 줄이세요</li>
                    <li>식사 일기를 작성해보세요</li>
                </ul>
            """, unsafe_allow_html=True)
        with col_exercise:
            st.markdown("""
                <div class="tip-header">운동 습관 🏃</div>
                <ul style="font-size:0.95rem; line-height:1.7;">
                    <li>엘리베이터 대신 계단 이용하기</li>
                    <li>하루 10,000보 걷기 목표</li>
                    <li>좋아하는 운동 찾기 (지속 가능성 중요)</li>
                    <li>운동 친구 만들기 (동기부여)</li>
                    <li>스트레칭으로 유연성 향상</li>
                </ul>
            """, unsafe_allow_html=True)

        st.divider()

        # 4. 분석 차트 및 로그
        tab1, tab2 = st.tabs(["📈 지표 추이 분석", "📋 상세 기록 로그"])
        with tab1:
            fig_bmi = px.line(user_df, x=COL_DATE, y=COL_BMI, markers=True, title="BMI 추이")
            st.plotly_chart(fig_bmi, use_container_width=True)
            fig_weight = px.line(user_df, x=COL_DATE, y=COL_WEIGHT, markers=True, title="체중 변화")
            st.plotly_chart(fig_weight, use_container_width=True)
        with tab2:
            st.dataframe(user_df.sort_values(COL_DATE, ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("💡 사용자를 선택하면 상세 건강 분석과 표준 범위를 확인할 수 있습니다.")
else:
    st.info("기록된 데이터가 없습니다. 사이드바에서 정보를 입력해 주세요.")