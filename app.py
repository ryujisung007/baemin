import streamlit as st
import google.generativeai as genai
import pandas as pd
from PyPDF2 import PdfReader
import io

# ==========================================
# 1. 초기 설정 및 보안
# ==========================================
st.set_page_config(page_title="R&D 전략 상황실 v2.0", layout="wide", page_icon="🎯")

# UI 커스텀 스타일링
st.markdown("""
    <style>
    .channel-box { border: 1px solid #d1d8e0; padding: 15px; border-radius: 10px; background-color: #ffffff; height: 650px; display: flex; flex-direction: column; }
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    .master-panel { background-color: #2c3e50; color: white; padding: 25px; border-radius: 12px; margin-bottom: 25px; }
    .chat-area { flex-grow: 1; overflow-y: auto; background: #f9f9f9; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)

# API 설정
with st.sidebar:
    st.title("🛡️ System Control")
    api_key = st.text_input("Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
    st.divider()
    st.caption("Senior R&D Specialist Mode Active")

# ==========================================
# 2. 데이터 처리 함수
# ==========================================
def extract_text(uploaded_file):
    """다양한 파일 형식에서 텍스트를 추출합니다."""
    if uploaded_file is None: return ""
    fname = uploaded_file.name
    try:
        if fname.endswith('.pdf'):
            reader = PdfReader(uploaded_file)
            return " ".join([page.extract_text() for page in reader.pages])
        elif fname.endswith(('.xlsx', '.csv')):
            df = pd.read_excel(uploaded_file) if fname.endswith('.xlsx') else pd.read_csv(uploaded_file)
            return df.to_string()
        else:
            return uploaded_file.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return f"파일 읽기 오류: {e}"

# ==========================================
# 3. 메인 화면 구성
# ==========================================

# 상단 통합 대시보드
st.markdown('<div class="master-panel">', unsafe_allow_html=True)
col_title, col_btn = st.columns([3, 1])
with col_title:
    st.subheader("🎯 통합 R&D 전략 마스터 대시보드")
    st.caption("하단 3개 분석실의 인사이트를 통합하여 최종 제품 설계안을 도출합니다.")

with col_btn:
    if st.button("🚀 3축 통합 전략 수립 시작"):
        # 3개 채널의 대화 요약본 수집 로직
        summaries = []
        for i in range(1, 4):
            hist = st.session_state.get(f'chat_hist_{i}', [])
            if hist:
                summaries.append(f"[채널 {i} 분석 요약]: {hist[-1][1]}")
        
        if len(summaries) < 3:
            st.warning("3개 채널의 분석이 모두 완료되어야 통합이 가능합니다.")
        else:
            with st.spinner("최종 시나리오 생성 중..."):
                final_prompt = f"다음 3가지 관점의 데이터를 통합하여 신제품 기획안과 초기 배합비를 설계해줘.\n\n" + "\n".join(summaries)
                response = model.generate_content(final_prompt)
                st.session_state.final_report = response.text
st.markdown('</div>', unsafe_allow_html=True)

if 'final_report' in st.session_state:
    with st.expander("📄 최종 통합 R&D 리포트 확인", expanded=True):
        st.markdown(st.session_state.final_report)

# 하단 3분할 채널
st.divider()
ch_cols = st.columns(3)
channels = [
    {"id": 1, "name": "🌍 거시경제 분석", "color": "#34495e"},
    {"id": 2, "name": "📊 음료시장 데이터", "color": "#2980b9"},
    {"id": 3, "name": "👥 소비자 태도조사", "color": "#8e44ad"}
]

for i, ch in enumerate(channels):
    with ch_cols[i]:
        st.markdown(f'<div class="channel-box" style="border-top: 5px solid {ch["color"]};">', unsafe_allow_html=True)
        st.subheader(ch["name"])
        
        # 1. 개별 파일 업로드 (찾아보기 버튼)
        up_file = st.file_uploader(f"파일 찾기 (채널 {ch['id']})", type=['pdf', 'xlsx', 'csv', 'txt'], key=f"file_{ch['id']}")
        
        if up_file:
            st.session_state[f"context_{ch['id']}"] = extract_text(up_file)
            st.success(f"✅ {up_file.name} 로드 완료")

        # 2. 채팅 기록 관리
        if f"chat_hist_{ch['id']}" not in st.session_state:
            st.session_state[f"chat_hist_{ch['id']}"] = []
        
        # 3. 개별 챗봇 인터페이스
        st.write("**분석 대화**")
        chat_container = st.container()
        with chat_container:
            st.markdown('<div class="chat-area">', unsafe_allow_html=True)
            for role, text in st.session_state[f"chat_hist_{ch['id']}"]:
                icon = "👤" if role == "user" else "🤖"
                st.write(f"{icon} {text}")
            st.markdown('</div>', unsafe_allow_html=True)

        # 질문 입력
        if user_input := st.chat_input(f"{ch['id']}번 질문 입력", key=f"input_{ch['id']}"):
            if not api_key:
                st.error("API Key가 필요합니다.")
            else:
                st.session_state[f"chat_hist_{ch['id']}"].append(("user", user_input))
                
                # RAG 로직: 파일 컨텍스트가 있으면 포함하여 질문
                context = st.session_state.get(f"context_{ch['id']}", "")
                full_query = f"다음 문서를 바탕으로 질문에 답해줘.\n\n[문서내용]\n{context[:5000]}\n\n질문: {user_input}"
                
                response = model.generate_content(full_query)
                st.session_state[f"chat_hist_{ch['id']}"].append(("assistant", response.text))
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# 초기화 버튼
if st.sidebar.button("🧹 모든 세션 초기화"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
