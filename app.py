import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import os

# 1. 시니어 전문가 모드 설정
st.set_page_config(page_title="Food R&D Expert System", layout="wide")

# API 로드 로직 (오류 점검 포함)
def get_api_keys():
    try:
        g_key = st.secrets["GOOGLE_API_KEY"]
        o_key = st.secrets["OPENAI_API_KEY"]
        return g_key, o_key
    except:
        return None, None

g_api_key, o_api_key = get_api_keys()

if not g_api_key or not o_api_key:
    st.error("⚠️ API 키가 설정되지 않았습니다. .streamlit/secrets.toml 또는 Cloud Secrets를 확인하세요.")
    st.stop()

# 2. AI 모델 초기화
genai.configure(api_key=g_api_key)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')
openai_client = OpenAI(api_key=o_api_key)

# 3. 핵심 기능: OpenAI 기반 식품 배합비 산출
def generate_formula(target_product):
    prompt = f"""
    식품공학 전문가로서 다음 제품의 표준 배합비를 작성하라: {target_product}
    1. 문헌 및 논문에 근거한 표준 배합비를 사용하되 표 형식으로 출력할 것.
    2. 표에는 [원료명, 배합비(%), 사용 목적, 용도, 용법, 사용주의사항] 칸을 반드시 포함할 것.
    3. 전문가적 소견으로 마케팅 전략도 간략히 첨언할 것.
    """
    # 응답이 빠르고 로드 부담이 적은 gpt-4o-mini 모델 사용
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "당신은 20년차 식품기술사이자 마케팅 전문가입니다."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# --- UI 구현 ---
st.title("🧪 식품 신제품 개발 AI 지원 시스템 (Senior Ver.)")
st.sidebar.header("📊 시스템 상태")
st.sidebar.success("Gemini 2.5 Flash 연결 완료")
st.sidebar.success("OpenAI gpt-4o-mini 연결 완료")

target = st.text_input("개발하고자 하는 신제품명을 입력하세요:", placeholder="예: 무설탕 비타민 전해질 음료")

if st.button("전문 분석 및 배합비 생성"):
    with st.spinner("AI 전문가들이 배합비와 전략을 구성 중입니다..."):
        # 1단계: Gemini 2.5 Flash를 이용한 시장 및 원료 트렌드 분석
        market_analysis = gemini_model.generate_content(f"{target}에 대한 최신 식품 소재 및 소비 트렌드 분석").text
        
        # 2단계: OpenAI를 이용한 정밀 배합비 산출 (지침 준수)
        formula_data = generate_formula(target)
        
        # 결과 출력
        st.subheader("💡 시장 트렌드 및 소재 분석 (Gemini)")
        st.write(market_analysis)
        
        st.divider()
        
        st.subheader("📝 표준 배합비 및 기술 검토 (OpenAI)")
        st.markdown(formula_data)

st.divider()
st.caption("© 2026 Food R&D Expert System - 시니어 AI 및 식품/포장기술사 설계")
