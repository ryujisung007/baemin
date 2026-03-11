import streamlit as st
import google.generativeai as genai
import os

# ==========================================
# 1. 초기 설정 및 보안 (Senior Dev Standard)
# ==========================================
st.set_page_config(
    page_title="Food R&D AI System",
    page_icon="🧪",
    layout="wide"
)

# [설정] 사용자 요청에 따른 모델 고정
# 환경에 따라 정식 명칭 'gemini-2.0-flash' 또는 'gemini-2.5-flash' 사용
MODEL_NAME = 'gemini-2.5-flash'

def initialize_agent():
    """AI 모델 초기화 및 API 키 검증"""
    try:
        # Streamlit Secrets 우선 참조
        if "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
        else:
            api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            st.error("⚠️ API 키가 설정되지 않았습니다. Secrets를 확인하세요.")
            return None
        
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(MODEL_NAME)
    except Exception as e:
        st.error(f"❌ 초기화 오류: {str(e)}")
        return None

# ==========================================
# 2. 메인 로직 함수
# ==========================================
def get_ai_response(model, prompt):
    """오류 점검 및 효율적 응답 생성"""
    try:
        # 응답 생성 (Fast Load 설정)
        response = model.generate_content(prompt)
        
        # [충돌 방지] 응답 후보군 존재 여부 체크
        if response and response.candidates:
            return response.text
        else:
            return "⚠️ AI가 응답을 생성했으나 안전 정책에 의해 차단되었거나 내용이 비어있습니다."
    except Exception as e:
        # 사소한 문법/논리 오류 방지를 위한 구체적 에러 메시지
        return f"❌ [시스템 에러] {type(e).__name__}: {str(e)}"

# ==========================================
# 3. Streamlit UI 레이아웃
# ==========================================
def main():
    st.title("🧪 식품 신제품 개발 AI 지원 시스템")
    st.caption("20년 차 시니어 AI 및 식품 공학 전문가 모드 가동 중")
    
    # 모델 초기화
    model = initialize_agent()
    
    if model:
        # 사이드바 설정
        with st.sidebar:
            st.header("⚙️ 분석 설정")
            st.info(f"현재 모델: {MODEL_NAME}")
            st.write("---")
            st.markdown("""
            **분석 가능 영역:**
            - 음료/식품 신제품 기획
            - 맛/원료 기반 소비빈도 분석
            - 표준 배합비 설계
            """)

        # 입력 영역
        st.subheader("📝 분석 요청")
        user_input = st.text_area(
            "분석할 원료 데이터나 마케팅 요구사항을 입력하세요.",
            height=250,
            placeholder="예: 40대 남성을 타겟으로 한 고단백 음료의 재구매 빈도를 높이기 위한 맛과 배합비 제안..."
        )

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("🚀 분석 실행", use_container_width=True):
                if user_input:
                    with st.spinner("Gemini 2.5 Flash가 데이터를 정밀 분석 중입니다..."):
                        # [핵심] 전체 수정한 부분: 로직의 효율성 및 오류 점검
                        result = get_ai_response(model, user_input)
                        
                        st.divider()
                        st.subheader("📊 분석 및 제안 결과")
                        st.markdown(result)
                        
                        # 결과 다운로드 기능 (Senior 가이드)
                        st.download_button(
                            label="결과 레포트 다운로드",
                            data=result,
                            file_name="food_rnd_report.md",
                            mime="text/markdown"
                        )
                else:
                    st.warning("분석할 내용을 입력해 주세요.")

if __name__ == "__main__":
    main()
