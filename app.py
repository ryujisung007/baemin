import streamlit as st
import google.generativeai as genai
import os

# [수정] 1. 페이지 설정 및 보안 설정
st.set_page_config(page_title="식품 R&D AI 시스템", layout="wide")

# [수정] 2. API 키 로드 (Streamlit Secrets 또는 환경 변수)
# 로컬 테스트 시에는 .streamlit/secrets.toml 파일에 저장하세요.
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("API 키를 찾을 수 없습니다. Streamlit Secrets 설정을 확인하세요.")
    st.stop()

genai.configure(api_key=api_key)

# [수정] 3. 모델 선언 - NotFound 에러 방지를 위해 명칭 확인
# 최신 안정 버전인 'gemini-1.5-flash'를 기본으로 사용합니다.
MODEL_NAME = 'gemini-1.5-flash'

def generate_ai_content(prompt):
    try:
        # 모델 객체 생성
        model = genai.GenerativeModel(MODEL_NAME)
        
        # 콘텐츠 생성 호출
        response = model.generate_content(prompt)
        
        # [체크] 응답 차단 여부 및 텍스트 존재 확인
        if response and response.candidates:
            return response.text
        else:
            return "AI가 응답을 생성했지만, 내용이 비어있거나 차단되었습니다."
            
    except Exception as e:
        # [에러 핸들링] NotFound 포함 모든 에러 메시지 출력
        return f"에러 발생 ({type(e).__name__}): {str(e)}"

# --- UI 레이아웃 ---
st.title("🧪 식품 신제품 개발 AI 지원 시스템")
st.info("식품연구원을 위한 맛, 원료 기반 소비빈도 및 배합비 분석 도구입니다.")

with st.sidebar:
    st.header("설정")
    target_model = st.selectbox("사용 모델 선택", [MODEL_NAME, "gemini-1.5-pro"])
    st.write("---")
    st.caption("20년 차 시니어 AI 전문가 모드 활성 중")

# 입력 영역
full_p = st.text_area("분석할 데이터나 페르소나, 요청사항을 입력하세요:", 
                     height=200, 
                     placeholder="예: 2030 여성을 타겟으로 한 저당 레몬 에이드의 소비 빈도를 높이기 위한 배합비 제안...")

if st.button("분석 실행"):
    if full_p:
        with st.spinner("데이터 분석 및 AI 응답 생성 중..."):
            # [수정] 94라인 근처 에러 발생 지점 보완 호출
            res = generate_ai_content(full_p)
            
            st.subheader("📌 분석 결과")
            st.markdown(res)
            
            # [시니어 팁] 결과 내보내기 기능 추가
            st.download_button("결과 저장(TXT)", res, file_name="rnd_analysis.txt")
    else:
        st.warning("분석할 내용을 입력해주세요.")

# --- 하단 정보 ---
st.write("---")
st.caption("© 2026 Food R&D AI System - Senior Developer Verified")
