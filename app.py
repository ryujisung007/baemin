import streamlit as st
import google.generativeai as genai
import pandas as pd
from PyPDF2 import PdfReader
import io

# [시니어 팁] 에러 방지를 위한 핵심 설정
st.set_page_config(page_title="R&D 전략 상황실", layout="wide")

# API 설정 (사이드바) - 모델 객체 생성을 함수화하여 에러 차단
def get_gemini_model(key):
    try:
        genai.configure(api_key=key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return None

with st.sidebar:
    st.title("🛡️ System Control")
    api_key = st.text_input("Gemini API Key", type="password")
    st.divider()
    
# 모델 객체 안전하게 확보
model = get_gemini_model(api_key) if api_key else None

# (중략: 기존 스타일링 및 텍스트 추출 함수 동일)
def extract_text(uploaded_file):
    if uploaded_file is None: return ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PdfReader(uploaded_file)
            text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
            return text if text.strip() else "PDF에서 텍스트를 추출할 수 없습니다."
        elif uploaded_file.name.endswith(('.xlsx', '.csv')):
            df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
            return df.to_string()
        return uploaded_file.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return ""

# 상단 통합 대시보드 (디자인 유지)
st.subheader("🎯 통합 R&D 전략 마스터 대시보드")

# 하단 3분할 채널 로직 수정
ch_cols = st.columns(3)
for i in range(1, 4):
    with ch_cols[i-1]:
        st.subheader(f"채널 {i}")
        up_file = st.file_uploader(f"파일 {i}", key=f"file_{i}")
        
        # 파일이 바뀔 때만 텍스트 추출 (메모리 효율화)
        if up_file:
            st.session_state[f"context_{i}"] = extract_text(up_file)

        if f"chat_hist_{i}" not in st.session_state:
            st.session_state[f"chat_hist_{i}"] = []

        # 질문 입력창 (모델이 있을 때만 활성화)
        if prompt := st.chat_input(f"채널 {i} 질문", key=f"input_{i}"):
            if not model:
                st.error("API Key를 먼저 입력해주세요.")
            else:
                st.session_state[f"chat_hist_{i}"].append(("user", prompt))
                
                # 컨텍스트가 비어있지 않은지 확인하는 안전 로직
                context = st.session_state.get(f"context_{i}", "첨부 파일 없음")
                full_query = f"파일 내용: {context[:10000]}\n\n질문: {prompt}"
                
                try:
                    # [핵심] API 호출 전 쿼리 검증
                    if prompt.strip():
                        response = model.generate_content(full_query)
                        st.session_state[f"chat_hist_{i}"].append(("assistant", response.text))
                        st.rerun()
                except Exception as api_err:
                    st.error(f"API 호출 오류: {api_err}")
