import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# 1. 설정 및 상수
DB_FILE = "health_analytics_v5.csv"
COL_DATE, COL_NAME, COL_WEIGHT, COL_BMI = "측정 일자", "성명", "체중(kg)", "BMI 지수"
COL_BMR, COL_BFP, COL_CALORIE = "기초대사량(kcal)", "체지방률(%)", "권장칼로리(kcal)"

st.set_page_config(page_title="Smart Health Analyzer Pro", layout="wide")

# CSS: 이미지 기반 스타일링 반영
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 15px; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #f0f0f0; }
    .advice-box { background-color: #f1fcf4; padding: 25px; border-radius: 12px; border-left: 6px solid #4caf50; }
    .delete-container { background-color: #fff5f5; padding: 20px; border-radius: 10px; border: 1px solid #feb2b2; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 처리 함수
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df[COL_DATE] = pd.to_datetime(df[COL_DATE]).dt.date
        return df
    return pd.DataFrame(columns=[COL_DATE, COL_NAME, COL_WEIGHT, COL_BMI, COL_BMR, COL_BFP, COL_CALORIE])

def get_standards(h, gen):
    min_w = round(18.5 * ((h/100)**2), 1)
    max_w = round(23.0 * ((h/100)**2), 1)
    std_bmr = "1,500~1,800" if gen == "남성" else "1,200~1,500"
    std_bfp = "15~25%" if gen == "남성" else "20~32%"
    return min_w, max_w, std_bmr, std_bfp

df = load_data()

# 3. 사이드바: 입력 및 전체 데이터 관리
with st.sidebar:
    st.header("👤 신규 정보 입력")
    with st.form("input_form"):
        u_date = st.date_input("측정 일자", datetime.date.today())
        u_name = st.text_input("성명")
        u_age = st.number_input("연령", 1, 100, 57)
        u_gen = st.radio("성별", ["남성", "여성"], horizontal=True)
        u_h = st.number_input("키(cm)", 100.0, 250.0, 175.0)
        u_w = st.number_input("체중(kg)", 30.0, 200.0, 70.0)
        submit = st.form_submit_button("기록 저장")

    if submit and u_name.strip():
        # 기본 분석 수치 계산
        bmi = round(u_w / ((u_h / 100) ** 2), 2)
        bmr = int((10 * u_w) + (6.25 * u_h) - (5 * u_age) + (5 if u_gen == "남성" else -161))
        bfp = round((1.20 * bmi) + (0.23 * u_age) - (16.2 if u_gen == "남성" else 5.4), 1)
        
        new_data = {COL_DATE: u_date, COL_NAME: u_name, COL_WEIGHT: u_w, COL_BMI: bmi, 
                    COL_BMR: bmr, COL_BFP: bfp, COL_CALORIE: int(bmr * 1.375)}
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        st.success(f"{u_name}님의 데이터가 저장되었습니다.")
        st.rerun()

    st.divider()
    st.header("📂 전체 데이터 관리")
    if not df.empty:
        # 전체 CSV 저장 기능
        full_csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 전체 DB CSV 다운로드", data=full_csv, file_name="full_health_db.csv", mime="text/csv")
        
        # 전체 삭제 기능 (관리자용)
        if st.button("🚨 전체 데이터 초기화", help="모든 사용자의 데이터가 삭제됩니다."):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
                st.rerun()

# 4. 메인 화면
st.title("🛡️ Mong's 건강 지킴이")

if not df.empty:
    user_list = sorted(df[COL_NAME].unique().tolist())
    selected_user = st.selectbox("🔍 대상자 선택", user_list, index=None, placeholder="조회할 성명을 선택하세요")
    
    if selected_user:
        user_df = df[df[COL_NAME] == selected_user].sort_values(COL_DATE)
        latest = user_df.iloc[-1]
        min_w, max_w, std_bmr, std_bfp = get_standards(u_h, u_gen)

        # 요약 지표 카드
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("현재 체중", f"{latest[COL_WEIGHT]} kg"); m1.caption(f"📍 표준: {min_w}~{max_w}kg")
        m2.metric("BMI", f"{latest[COL_BMI]}"); m2.caption("📍 표준: 18.5~23.0")
        m3.metric("기초대사량", f"{latest[COL_BMR]:,} kcal"); m3.caption(f"📍 평균: {std_bmr}kcal")
        m4.metric("체지방률", f"{latest[COL_BFP]} %"); m4.caption(f"📍 표준: {std_bfp}")

        st.divider()

        # 통합 그래프
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=user_df[COL_DATE], y=user_df[COL_WEIGHT], name="체중(kg)", mode='lines+markers', line=dict(color='#2196F3', width=3)), secondary_y=False)
        fig.add_trace(go.Scatter(x=user_df[COL_DATE], y=user_df[COL_BMI], name="BMI", mode='lines+markers', line=dict(color='#FF9800', width=3, dash='dot')), secondary_y=True)
        fig.update_layout(title=f"<b>{selected_user}</b>님의 건강 지표 변화", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # 맞춤 조언 및 팁
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

        st.write("")

        # 5. 데이터 관리 섹션
        with st.expander("🛠️ 데이터 관리 (삭제 및 개별 저장)"):
            st.markdown('<div class="delete-container">', unsafe_allow_html=True)
            
            # (1) 선택적 CSV 저장
            u_csv = user_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(f"📥 {selected_user}님 데이터만 저장", data=u_csv, file_name=f"health_{selected_user}.csv", mime="text/csv")
            
            st.write("---")
            
            # (2) 선택적 삭제 (특정 날짜 기록)
            st.subheader("🗑️ 선택적 삭제")
            dates = user_df[COL_DATE].tolist()
            target_date = st.selectbox("삭제할 기록의 날짜를 선택하세요", dates)
            if st.button("선택한 날짜 기록 삭제"):
                df = df.drop(df[(df[COL_NAME] == selected_user) & (df[COL_DATE] == target_date)].index)
                df.to_csv(DB_FILE, index=False)
                st.success(f"{target_date} 기록이 삭제되었습니다.")
                st.rerun()

            # (3) 사용자 전체 삭제
            st.write("---")
            st.subheader("🔥 사용자 전체 삭제")
            if st.button(f"{selected_user}님의 모든 데이터 삭제"):
                df = df[df[COL_NAME] != selected_user]
                df.to_csv(DB_FILE, index=False)
                st.warning(f"{selected_user}님의 모든 기록이 제거되었습니다.")
                st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

            st.write("### 📋 기록 로그")
            st.dataframe(user_df.sort_values(COL_DATE, ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("💡 사용자를 선택하면 상세 지표와 관리 메뉴가 나타납니다.")
else:
    st.info("기록된 데이터가 없습니다. 사이드바에서 정보를 입력해 주세요.")