import streamlit as st
import google.generativeai as genai
import pandas as pd
from PyPDF2 import PdfReader
import io

st.set_page_config(page_title="R&D 전략 상황실 v2.5", layout="wide", page_icon="🎯")

# --- 스타일링 ---
st.markdown("""
    <style>
    .channel-box { border: 2px solid #e9ecef; padding: 15px; border-radius: 12px; background-color: #ffffff; height: 700px; display: flex; flex-direction: column; }
    .master-panel { background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: white; padding: 20px; border-radius: 15px; margin-bottom: 25px; }
    .chat-area { flex-grow: 1; overflow-y: auto; background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #f1f5f9; margin-bottom: 10px; font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)

# --- API 설정 ---
with st.sidebar:
    st.title("🛡️ System Control")
    api_key = st.text_input("Gemini API Key", type="password")
    st.divider()
    if api_key:
        genai.configure(api_key=api_key)
        # 최신 모델 우선 할당
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            st.success("✅ Gemini 2.0 Flash 연결됨")
        except:
            model = genai.GenerativeModel('gemini-1.5-flash')
            st.info("ℹ️ Gemini 1.5 Flash로 연결됨")
    else:
        model = None

# --- 데이터 추출기 ---
def extract_text(uploaded_file):
    if not uploaded_file: return ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            return " ".join([p.extract_text() for p in PdfReader(uploaded_file).pages if p.extract_text()])
        elif uploaded_file.name.endswith(('.xlsx', '.csv')):
            df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
            return df.to_string()
        return uploaded_file.read().decode('utf-8', errors='ignore')
    except: return "텍스트 추출 실패"

# --- 상단 대시보드 ---
st.markdown('<div class="master-panel">', unsafe_allow_html=True)
c1, c2 = st.columns([3, 1])
with c1:
    st.header("🎯 통합 R&D 전략 마스터 대시보드")
    st.write("하단 3분할 채널에서 도출된 개별 인사이트를 융합하여 최종 제품을 기획합니다.")
with c2:
    if st.button("🚀 통합 전략 및 제품 설계"):
        summaries = [st.session_state.get(f"chat_hist_{i}", [("", "내용 없음")])[-1][1] for i in range(1, 4)]
        with st.spinner("Gemini 2.0 기반 교차 분석 중..."):
            prompt = f"거시경제, 시장데이터, 소비자조사 결과를 통합하여 차세대 음료 제품 기획서와 가상 배합비를 써줘.\n\n분석요약:\n{summaries}"
            st.session_state.final_res = model.generate_content(prompt).text
st.markdown('</div>', unsafe_allow_html=True)

if 'final_res' in st.session_state:
    st.expander("📄 최종 통합 리포트 확인", expanded=True).markdown(st.session_state.final_res)

# --- 하단 3분할 채널 ---
cols = st.columns(3)
titles = ["🌍 거시경제", "📊 음료시장", "👥 소비자조사"]

for i in range(3):
    idx = i + 1
    with cols[i]:
        st.markdown(f'<div class="channel-box">', unsafe_allow_html=True)
        st.subheader(titles[i])
        
        # 업로드 버튼 (찾아보기)
        f = st.file_uploader(f"파일 찾기 (CH{idx})", key=f"f_{idx}")
        if f: st.session_state[f"ctx_{idx}"] = extract_text(f)

        # 채팅 이력
        if f"chat_hist_{idx}" not in st.session_state:
            st.session_state[f"chat_hist_{idx}"] = [("assistant", f"안녕하세요! {titles[i]} 분석을 시작할까요?")]
        
        # 채팅창 표시
        st.markdown('<div class="chat-area">', unsafe_allow_html=True)
        for r, t in st.session_state[f"chat_hist_{idx}"]:
            st.write(f"{'👤' if r=='user' else '🤖'} {t}")
        st.markdown('</div>', unsafe_allow_html=True)

        # 입력창
        if p := st.chat_input(f"{titles[i]} 질문", key=f"in_{idx}"):
            if model:
                st.session_state[f"chat_hist_{idx}"].append(("user", p))
                ctx = st.session_state.get(f"ctx_{idx}", "")
                full_p = f"문서내용: {ctx[:8000]}\n\n질문: {p}"
                res = model.generate_content(full_p).text
                st.session_state[f"chat_hist_{idx}"].append(("assistant", res))
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
