import streamlit as st
import google.generativeai as genai
import PyPDF2  # PDF 분석을 위한 라이브러리 추가

# 1. 시니어 AI 전문가의 설정
st.set_page_config(page_title="식품 트렌드 분석 전문가", layout="wide")

# API 키 세팅
if "GEMINI_API_KEY" not in st.session_state:
    st.session_state.GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

# 2. 세션 상태 관리 (충돌 방지 및 메모리 유지)
def init_state():
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    if "final_report" not in st.session_state: st.session_state.final_report = "아직 작성된 보고서가 없습니다."
    if "raw_content" not in st.session_state: st.session_state.raw_content = ""
    if "doc_structure" not in st.session_state: st.session_state.doc_structure = ""

init_state()

# 모델 로드 (API 키 존재 시)
if st.session_state.GEMINI_API_KEY:
    genai.configure(api_key=st.session_state.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    st.sidebar.warning("API 키를 입력해주세요.")

# --- UI 레이아웃 ---
st.title("🍎 식품 시장 트렌드 분석 및 실시간 보고서 시스템")

with st.sidebar:
    st.header("⚙️ 환경 설정")
    if not st.session_state.GEMINI_API_KEY:
        key_input = st.text_input("Enter Gemini API Key", type="password")
        if key_input:
            st.session_state.GEMINI_API_KEY = key_input
            st.rerun()

    # PDF 지원을 위해 type에 "pdf" 추가
    uploaded_file = st.file_uploader("자료 업로드 (TXT, PDF)", type=["txt", "pdf"])
    
    if uploaded_file and st.button("📊 전체 구조 분석"):
        # 파일 형식에 따른 텍스트 추출 로직
        if uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            content = ""
            for page in pdf_reader.pages:
                content += page.extract_text()
        else:
            content = uploaded_file.getvalue().decode("utf-8")
            
        st.session_state.raw_content = content
        
        with st.spinner("구조 파악 중..."):
            prompt = f"다음 자료의 목차 구조와 핵심 리스트를 분석해줘:\n\n{content[:3000]}"
            st.session_state.doc_structure = model.generate_content(prompt).text
            st.success("구조 분석 완료")

    if st.session_state.doc_structure:
        st.divider()
        st.subheader("📑 분석된 문서 구조")
        st.info(st.session_state.doc_structure)

# 메인 업무 영역
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💬 분석 및 보고서 작성")
    for role, text in st.session_state.chat_history:
        with st.chat_message(role):
            # 화면에는 대화 파트만 표시 ([REPORT_UPDATE] 이전 내용)
            display_text = text.split("[REPORT_UPDATE]")[0] if "[REPORT_UPDATE]" in text else text
            st.markdown(display_text)

    if user_input := st.chat_input("보고서 내용을 요청하세요"):
        st.session_state.chat_history.append(("user", user_input))
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            sys_msg = (
                "당신은 20년 경력의 시니어 식품 분석가입니다. 사용자와 대화하며 보고서를 완성하세요. "
                "응답 끝에는 반드시 [REPORT_UPDATE] 태그와 함께 현재까지 완성된 전체 보고서 본문을 적으세요."
            )
            context = f"원본자료: {st.session_state.raw_content[:2000]}\n현재보고서: {st.session_state.final_report}\n요청: {user_input}"
            
            response = model.generate_content(f"{sys_msg}\n\n{context}")
            full_res = response.text
            
            if "[REPORT_UPDATE]" in full_res:
                chat_p, report_p = full_res.split("[REPORT_UPDATE]")
                st.session_state.final_report = report_p.strip()
                st.markdown(chat_p.strip())
            else:
                st.markdown(full_res)
            
            st.session_state.chat_history.append(("assistant", full_res))

with col2:
    st.subheader("📝 최종 보고서 실시간 뷰")
    st.markdown(
        f"""<div style="border:1px solid #ddd; padding:20px; border-radius:10px; height:500px; overflow-y:auto; background-color:#fff;">
        {st.session_state.final_report}
        </div>""", unsafe_allow_html=True
    )

# 5번 기능: 검색 및 특정 위치 구조 보고
st.divider()
st.subheader("🔎 정보 탐색 및 데이터 구조 리포트")
search_q = st.text_input("자료에서 특정 키워드 검색")
if search_q and st.session_state.raw_content:
    with st.spinner("데이터 분석 중..."):
        s_prompt = f"'{search_q}'에 대해 요약하고, 해당 자료가 위치한 페이지/섹션의 구조(리스트, 표 등)를 보고해줘.\n\n자료: {st.session_state.raw_content[:4000]}"
        st.write(model.generate_content(s_prompt).text)
