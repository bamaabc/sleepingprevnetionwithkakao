
import streamlit as st
import time
import numpy as np
import pandas as pd
import requests
import webbrowser

st.set_page_config(page_title="졸음운전 경로 안내 시스템", layout="centered")
st.title("🧠 실시간 졸음운전 감지 + 카카오내비 연동 시스템")

KAKAO_API_KEY = "ab01e437adf3fbd1765cbcb61b455e5b"  # 실제 카카오 API 키 포함

# 졸음 분류 함수
def classify_drowsiness(theta, alpha):
    ratio = (theta / alpha) * 100
    if ratio < 30:
        return ratio, "각성", 0
    elif ratio < 60:
        return ratio, "경계", 1
    elif ratio < 80:
        return ratio, "졸음", 2
    else:
        return ratio, "위험", 3

# 카카오맵에서 휴게소 검색
def search_nearest_rest_area(lat, lng, radius=20000, query="휴게소"):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = { "Authorization": f"KakaoAK {KAKAO_API_KEY}" }
    params = { "query": query, "x": lng, "y": lat, "radius": radius, "sort": "distance" }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        documents = response.json().get("documents", [])
        if documents:
            rest = documents[0]
            return {
                "name": rest["place_name"],
                "lat": rest["y"],
                "lng": rest["x"]
            }
    return None

# 카카오내비 열기 (모바일용)
def open_kakaonavi_navigation(dest_lat, dest_lng, dest_name="휴게소"):
    url = f'kakaonavi://navigate?dest_lat={dest_lat}&dest_lng={dest_lng}&dest_name={dest_name}'
    webbrowser.open(url)

# 초기 상태 설정
if "running" not in st.session_state:
    st.session_state.running = False
if "data" not in st.session_state:
    st.session_state.data = []

st.subheader("🚗 운전 위치 설정")
current_lat = st.number_input("현재 위도", value=37.498004)
current_lng = st.number_input("현재 경도", value=127.027706)

if st.button("🟢 운전 시작"):
    st.session_state.running = True
    st.session_state.data = []

# 시뮬레이션 실행
if st.session_state.running:
    st.subheader("📡 실시간 EEG 감지 중...")
    chart = st.line_chart()
    triggered = False

    for i in range(60):
        theta = np.random.uniform(10, 30)
        alpha = np.random.uniform(20, 50)
        score, state, level = classify_drowsiness(theta, alpha)

        st.session_state.data.append({
            "시간": pd.Timestamp.now().strftime("%H:%M:%S"),
            "세타": theta,
            "알파": alpha,
            "졸음지수": score,
            "상태": state,
            "자율단계": level
        })

        chart.add_rows({"졸음지수": [score]})
        st.markdown(f"**현재 졸음 상태:** `{state}` / **자율운전 단계:** `Level {level}`")

        if level >= 2 and not triggered:
            st.error("⚠️ 졸음 위험 감지됨! 가장 가까운 휴게소로 안내합니다.")
            rest_info = search_nearest_rest_area(current_lat, current_lng)
            if rest_info:
                st.success(f"📍 안내 대상: {rest_info['name']}")
                st.markdown(f"[카카오내비로 열기](kakaonavi://navigate?dest_lat={rest_info['lat']}&dest_lng={rest_info['lng']}&dest_name={rest_info['name']})")
            else:
                st.warning("❗ 근처에 휴게소를 찾을 수 없습니다.")
            triggered = True
        time.sleep(0.3)

    st.success("✅ 시뮬레이션 완료!")
    df = pd.DataFrame(st.session_state.data)
    st.line_chart(df[["졸음지수"]])
    st.dataframe(df)
