import streamlit as st
import google.generativeai as genai

# 1. 환경 설정 및 모델 초기화
st.set_page_config(page_title="Food Trend Senior Analyst", layout="wide")

# API 키는 보안을 위해 secrets에서 관리하거나 직접 입력
if "GEMINI_API_KEY" not in st.session_state:
    st.session_state.GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

# API 키가 있을 경우에만 모델 설정
if st.session_state.GEMINI_API_KEY:
    genai.configure(api_key=st.session_state.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    st.warning("Sidebar에서 Gemini API Key를 입력해주세요.")

# 2. 세션 상태 관리 (데이터 유실 방지)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "final_report" not in st.session_state:
    st.session_state.final_report = "작성된 보고서 내용이 여기에 표시됩니다."
if "doc_structure" not in st.session_state:
    st.session_state.doc_structure = ""
if "raw_content" not in st.session_state:
    st.session_state.raw_content = ""

# --- UI 레이아웃 ---
st.title("📊 식품 시장 트렌드 분석 및 실시간 보고서 생성")

with st.sidebar:
    st.header("⚙️ 설정 및 업로드")
    if not st.session_state.GEMINI_API_KEY:
        api_key = st.text_input("Gemini API Key", type="password")
        if api_key:
            st.session_state.GEMINI_API_KEY = api_key
            st.rerun()

    uploaded_file = st.file_uploader("트렌드 자료 업로드 (TXT, MD 등)", type=["txt", "md"])
    if uploaded_file:
        st.session_state.raw_content = uploaded_file.getvalue().decode("utf-8")
        if st.button("🔍 자료 구조 및 리스트 분석"):
            with st.spinner("분석 중..."):
                prompt = f"다음 자료의 구조와 포함된 리스트 항목을 분석해줘:\n\n{st.session_state.raw_content[:4000]}"
                st.session_state.doc_structure = model.generate_content(prompt).text
                st.success("분석 완료")
    
    if st.session_state.doc_structure:
        st.divider()
        st.subheader("🏗️ 파악된 자료 구조")
        st.info(st.session_state.doc_structure)

# 메인 업무 영역 (2열 구성)
col_chat, col_report = st.columns([1, 1])

with col_chat:
    st.subheader("💬 전문가와 대화")
    # 대화 이력 표시
    for role, text in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(text)

    if user_input := st.chat_input("보고서 내용을 다듬어달라고 요청하세요."):
        st.session_state.chat_history.append(("user", user_input))
        with st.chat_message("user"):
            st.markdown(user_input)

        # Gemini 호출 및 보고서 업데이트 로직
        with st.chat_message("assistant"):
            sys_instr = (
                "당신은 식품 분석 전문가입니다. 사용자의 요청을 반영하여 보고서를 작성하세요. "
                "응답 마지막에 반드시 [REPORT_UPDATE] 태그를 적고 그 뒤에 현재까지 완성된 전체 보고서 내용을 덧붙여주세요."
            )
            context = f"원본자료: {st.session_state.raw_content[:2000]}\n현재보고서: {st.session_state.final_report}\n사용자요청: {user_input}"
            
            response = model.generate_content(f"{sys_instr}\n\n{context}")
            full_text = response.text
            
            # 보고서 부분 분리
            if "[REPORT_UPDATE]" in full_text:
                chat_msg, report_msg = full_text.split("[REPORT_UPDATE]")
                st.session_state.final_report = report_msg.strip()
                st.markdown(chat_msg.strip())
            else:
                st.markdown(full_text)
            
            st.session_state.chat_history.append(("assistant", full_text))

with col_report:
    st.subheader("📝 최종 트렌드 보고서")
    # 수정된 보고서 실시간 렌더링
    st.markdown(
        f"""
        <div style="border: 1px solid #ddd; padding: 20px; border-radius: 8px; background-color: #fcfcfc; min-height: 500px;">
            {st.session_state.final_report}
        </div>
        """, 
        unsafe_allow_html=True
    )

# 5번 기능: 특정 내용 검색 및 해당 페이지 구조 보고
st.divider()
st.subheader("🔎 특정 정보 및 데이터 구조 리포트")
search_query = st.text_input("자료에서 찾고 싶은 키워드 입력")

if search_query and st.session_state.raw_content:
    with st.spinner("자료를 뒤지는 중..."):
        search_prompt = (
            f"자료 내에서 '{search_query}'를 찾아 요약하고, "
            f"그 내용이 들어있는 부분의 자료 구조(표인지, 리스트인지 등)를 설명해줘.\n\n"
            f"원본: {st.session_state.raw_content[:5000]}"
        )
        search_res = model.generate_content(search_prompt).text
        st.write(search_res)
