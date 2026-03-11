"""
🔬 음료 트렌드 분석 & 배합 설계 플랫폼
Gemini 2.5 Flash + ChromaDB RAG
"""
import streamlit as st
import time, json, os
from rag_engine import (
    configure_gemini,
    get_flash_model,
    extract_text_from_file,
    chunk_text,
    tag_topics_batch,
    RAGVectorStore,
    chat_with_rag,
    generate_auto_summary,
    extract_report_section,
    load_beverage_db,
    beverage_db_to_text,
    generate_pdf_report,
    generate_integrated_analysis,
    SYSTEM_PROMPTS,
)

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(
    page_title="🔬 음료 트렌드 분석 플랫폼",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 커스텀 CSS
# ============================================================
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp { background-color: #f8fafc; }
    
    /* 사이드바 */
    [data-testid="stSidebar"] { background-color: #1e293b; }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li,
    [data-testid="stSidebar"] .stMarkdown span {
        color: #e2e8f0 !important;
    }
    
    /* 챗 버블 */
    .chat-user {
        background: #3b82f6; color: white;
        padding: 8px 12px; border-radius: 12px 12px 4px 12px;
        margin: 4px 0; max-width: 85%; margin-left: auto;
        font-size: 13px; line-height: 1.6;
    }
    .chat-ai {
        background: #f1f5f9; color: #1e293b;
        padding: 8px 12px; border-radius: 12px 12px 12px 4px;
        margin: 4px 0; max-width: 85%;
        font-size: 13px; line-height: 1.6; white-space: pre-wrap;
    }
    
    /* 보고서 섹션 */
    .report-section {
        background: white; border: 1px solid #e2e8f0;
        border-radius: 8px; padding: 12px; margin-bottom: 10px;
    }
    .report-section-new {
        background: #fefce8; border: 1px solid #fde047;
        border-radius: 8px; padding: 12px; margin-bottom: 10px;
    }
    .report-num {
        background: #2563eb; color: white;
        padding: 1px 8px; border-radius: 4px;
        font-size: 11px; font-weight: 700;
    }
    
    /* 키워드 태그 */
    .keyword-tag {
        background: #eff6ff; color: #2563eb;
        padding: 2px 8px; border-radius: 10px;
        font-size: 11px; font-weight: 500;
        display: inline-block; margin: 2px;
    }
    
    /* 섹션 헤더바 */
    .section-header {
        background: #1e293b; color: white;
        padding: 6px 12px; border-radius: 7px 7px 0 0;
        font-weight: 700; font-size: 13px;
    }
    .section-header-blue {
        background: #2563eb; color: white;
        padding: 6px 12px; border-radius: 7px 7px 0 0;
        font-weight: 700; font-size: 13px;
    }
    .section-header-purple {
        background: #7c3aed; color: white;
        padding: 6px 12px; border-radius: 7px 7px 0 0;
        font-weight: 700; font-size: 13px;
    }
    
    /* 추천 질문 칩 */
    div.stButton > button[kind="secondary"] {
        background: #eff6ff !important;
        color: #2563eb !important;
        border: 1px solid #bfdbfe !important;
        border-radius: 16px !important;
        font-size: 12px !important;
        padding: 4px 12px !important;
    }
    
    /* 스크롤 컨테이너 */
    .scroll-container {
        max-height: 400px; overflow-y: auto;
        border: 1px solid #e2e8f0;
        background: white; padding: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 세션 상태 초기화
# ============================================================
def init_session():
    defaults = {
        # API
        "gemini_api_key": "",
        "api_configured": False,
        "vector_store": None,
        # 페이지
        "current_page": "home",
        # 카테고리별 상태
        "uploads": {"macro": None, "beverage": None, "consumer": None},
        "raw_texts": {"macro": "", "beverage": "", "consumer": ""},
        "summaries": {"macro": "", "beverage": "", "consumer": ""},
        "keywords": {"macro": [], "beverage": [], "consumer": []},
        "file_info": {"macro": {}, "beverage": {}, "consumer": {}},
        "indexed": {"macro": False, "beverage": False, "consumer": False},
        # 챗 히스토리
        "chat_macro": [],
        "chat_beverage": [],
        "chat_consumer": [],
        "chat_formula": [],
        "chat_report": [],
        # 보고서 섹션
        "report_macro": [],
        "report_beverage": [],
        "report_consumer": [],
        "report_formula": [],
        "report_report": [],
        "report_integrated": [],
        # 음료 DB
        "beverage_db": None,
        "beverage_db_loaded": False,
        # 토픽 필터
        "topic_filter_macro": "전체",
        "topic_filter_beverage": "전체",
        "topic_filter_consumer": "전체",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session()


# ============================================================
# 유틸리티 함수
# ============================================================
def render_chat_bubble(role: str, content: str):
    """챗 버블 렌더링"""
    if role == "user":
        st.markdown(f'<div style="text-align:right"><div class="chat-user">{content}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-ai">{content}</div>', unsafe_allow_html=True)


def render_report_section(section: dict):
    """보고서 섹션 렌더링"""
    cls = "report-section-new" if section.get("is_new") else "report-section"
    new_badge = '<span style="background:#f59e0b;color:white;font-size:9px;padding:1px 5px;border-radius:3px;margin-left:6px;">NEW</span>' if section.get("is_new") else ""
    st.markdown(f"""
    <div class="{cls}">
        <div style="margin-bottom:6px;">
            <span class="report-num">{section['number']}</span>
            <strong style="margin-left:6px;font-size:13px;">{section['title']}</strong>
            {new_badge}
        </div>
        <div style="font-size:12px;color:#334155;line-height:1.7;white-space:pre-wrap;">{section['content']}</div>
    </div>
    """, unsafe_allow_html=True)


def process_upload(uploaded_file, category: str):
    """파일 업로드 처리 파이프라인"""
    try:
        with st.spinner("📄 텍스트 추출 중..."):
            file_bytes = uploaded_file.read()
            raw_text = extract_text_from_file(file_bytes, uploaded_file.name)
            st.session_state.raw_texts[category] = raw_text
            st.session_state.file_info[category] = {
                "name": uploaded_file.name,
                "size": f"{len(file_bytes) / 1024 / 1024:.1f}MB",
            }

        with st.spinner("📝 AI 자동 요약 생성 중..."):
            summary, keywords = generate_auto_summary(raw_text, category)
            st.session_state.summaries[category] = summary
            st.session_state.keywords[category] = keywords

        with st.spinner("🔗 청킹 & 토픽 태깅 중..."):
            chunks = chunk_text(raw_text)
            try:
                tagged_chunks = tag_topics_batch(chunks, category)
            except Exception:
                # 태깅 실패 시 기본 태그로 진행
                tagged_chunks = chunks
                for c in tagged_chunks:
                    c["topics"] = ["기타"]
                    c["category"] = category

        with st.spinner("📊 벡터DB 인덱싱 중..."):
            vs = st.session_state.vector_store
            vs.clear_collection(category)
            vs.add_chunks(category, tagged_chunks)
            st.session_state.indexed[category] = True

        st.session_state.uploads[category] = True

    except Exception as e:
        st.error(f"❌ 업로드 처리 중 오류: {str(e)}")
        st.info("💡 Gemini API Key가 올바른지 확인해주세요.")
        import traceback
        st.code(traceback.format_exc(), language="text")


def handle_chat(query: str, category: str, topic_filter: str = "전체", extra_collections=None):
    """챗봇 질의 처리 + 보고서 섹션 생성"""
    chat_key = f"chat_{category}"
    report_key = f"report_{category}"

    # 사용자 메시지 추가
    st.session_state[chat_key].append({"role": "user", "content": query})

    # RAG 챗봇 응답
    with st.spinner("🤖 Gemini 분석 중..."):
        response = chat_with_rag(
            query=query,
            vector_store=st.session_state.vector_store,
            collection_name=category,
            chat_history=st.session_state[chat_key],
            topic_filter=topic_filter,
            extra_collections=extra_collections,
        )

    # AI 응답 추가
    st.session_state[chat_key].append({"role": "ai", "content": response})

    # 보고서 섹션 자동 추출
    existing = st.session_state[report_key]
    cat_prefix = {"macro": "1", "beverage": "2", "consumer": "3", "formula": "4", "report": ""}
    prefix = cat_prefix.get(category, "")
    section_num = f"{prefix}.{len(existing) + 1}" if prefix else f"{len(existing) + 1}"

    with st.spinner("📋 보고서 섹션 생성 중..."):
        section = extract_report_section(response, section_num)
        if section:
            # 기존 섹션 is_new 해제
            for s in existing:
                s["is_new"] = False
            st.session_state[report_key].append(section)


# ============================================================
# 사이드바
# ============================================================
with st.sidebar:
    st.markdown("## 🔬 Trend Analyzer")
    st.caption("Gemini 2.5 Flash + ChromaDB RAG")
    st.markdown("---")

    # API 키 입력
    api_key = st.text_input(
        "🔑 Gemini API Key",
        type="password",
        value=st.session_state.gemini_api_key,
        placeholder="AIza...",
    )
    if api_key and api_key != st.session_state.gemini_api_key:
        st.session_state.gemini_api_key = api_key
        try:
            configure_gemini(api_key)
            st.session_state.vector_store = RAGVectorStore(api_key)
            # 모델 접근 테스트
            model = get_flash_model()
            import rag_engine
            model_name = rag_engine._verified_model_name or "flash"
            st.session_state.api_configured = True
            st.success(f"✅ API 연결 완료 ({model_name})")
        except Exception as e:
            st.session_state.api_configured = False
            st.error(f"❌ API 연결 실패: {str(e)}")
    elif api_key and st.session_state.api_configured:
        st.success("✅ API 연결됨")

    st.markdown("---")

    # 네비게이션
    pages = {
        "🏠 홈": "home",
        "📊 거시시장 분석": "macro",
        "🥤 음료시장 분석": "beverage",
        "👥 소비자 태도 분석": "consumer",
        "🧪 음료 DB & 배합비": "formula",
        "📋 통합 분석 보고서": "report",
    }

    for label, key in pages.items():
        # 상태 표시
        status = ""
        if key in ["macro", "beverage", "consumer"]:
            if st.session_state.indexed.get(key):
                status = " ✅"
        elif key == "formula":
            if st.session_state.beverage_db_loaded:
                status = " ✅"

        if st.button(f"{label}{status}", key=f"nav_{key}", use_container_width=True):
            st.session_state.current_page = key
            st.rerun()

    st.markdown("---")
    st.caption("ChromaDB · Gemini 2.5 Flash")
    st.caption("PDF RAG · v1.0")


# ============================================================
# API 키 체크
# ============================================================
def check_api():
    if not st.session_state.api_configured:
        st.warning("⚠️ 사이드바에서 Gemini API Key를 입력해주세요.")
        st.info("Google AI Studio에서 무료 API 키를 발급받을 수 있습니다: https://aistudio.google.com/app/apikey")
        return False
    return True


# ============================================================
# 📄 HOME PAGE
# ============================================================
def page_home():
    # 헤더
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1e3a5f,#2563eb);border-radius:14px;padding:24px 20px;color:white;margin-bottom:16px;">
        <h2 style="margin:0;font-size:22px;">🔬 음료 트렌드 분석 & 배합 설계 플랫폼</h2>
        <p style="margin:6px 0 0;font-size:13px;opacity:0.85;">
            PDF 업로드 → AI 챗봇 대화 → 실시간 보고서 → 배합비 유추까지 원스톱
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not check_api():
        return

    # 워크플로우
    st.markdown("#### 🔄 워크플로우")
    cols = st.columns(5)
    steps = [
        ("① PDF 업로드", "3개 보고서", "#dbeafe"),
        ("② AI 자동 요약", "텍스트 추출+요약", "#dcfce7"),
        ("③ 챗봇 분석", "RAG 기반 Q&A", "#fef3c7"),
        ("④ 보고서 작성", "실시간 빌드", "#fae8ff"),
        ("⑤ 통합+배합비", "크로스 분석", "#fef2f2"),
    ]
    for col, (title, desc, bg) in zip(cols, steps):
        col.markdown(f"""
        <div style="background:{bg};border-radius:8px;padding:10px;text-align:center;min-height:70px;">
            <div style="font-weight:700;font-size:12px;">{title}</div>
            <div style="font-size:10px;color:#64748b;margin-top:4px;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 업로드 현황
    st.markdown("#### 📡 분석 현황")
    cols = st.columns(4)
    statuses = [
        ("📊 거시시장", "macro", ["건강웰니스", "경기침체", "ESG"]),
        ("🥤 음료시장", "beverage", ["프로바이오틱스", "제로슈거", "식물성"]),
        ("👥 소비자태도", "consumer", ["건강기능성↑", "클린라벨", "MZ세대"]),
        ("🧪 음료 DB", "formula_db", ["원료 174종", "제품 321건", "배합 200건"]),
    ]
    for col, (label, key, tags) in zip(cols, statuses):
        if key == "formula_db":
            is_done = st.session_state.beverage_db_loaded
            status_text = "연결됨" if is_done else "대기"
            status_color = "#2563eb" if is_done else "#f59e0b"
        else:
            is_done = st.session_state.indexed.get(key, False)
            status_text = "완료" if is_done else "대기"
            status_color = "#10b981" if is_done else "#f59e0b"

        tag_html = " ".join([f'<span class="keyword-tag">{t}</span>' for t in tags])
        col.markdown(f"""
        <div style="background:white;border:1px solid #e2e8f0;border-radius:10px;padding:12px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <strong style="font-size:13px;">{label}</strong>
                <span style="background:{status_color};color:white;font-size:10px;padding:2px 8px;border-radius:10px;">{status_text}</span>
            </div>
            <div style="margin-top:6px;">{tag_html}</div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# 📊🥤👥 ANALYSIS PAGE (공통)
# ============================================================
def page_analysis(category: str, title: str, icon: str, color: str):
    if not check_api():
        return

    chat_key = f"chat_{category}"
    report_key = f"report_{category}"
    filter_key = f"topic_filter_{category}"

    topic_options = {
        "macro": ["전체", "음료산업", "경제지표", "인구사회", "규제정책", "환경ESG", "건강웰니스"],
        "beverage": ["전체", "탄산음료", "비탄산음료", "기능성음료", "RTD커피차", "유제품음료", "식물성음료", "시장규모", "브랜드분석"],
        "consumer": ["전체", "구매동기", "연령별", "성별", "채널별", "가격민감도", "건강관심", "트렌드인식"],
    }

    suggest_questions = {
        "macro": ["음료 관련 트렌드만 요약해줘", "경기침체가 음료시장에 미치는 영향은?", "인구구조 변화와 음료 소비 관계는?", "ESG 규제가 포장에 미치는 영향은?"],
        "beverage": ["성장 빠른 카테고리 TOP 5는?", "프로바이오틱스 시장 심층 분석해줘", "유통채널별 트렌드는?", "제로슈거 시장 규모와 전망은?"],
        "consumer": ["구매 결정 요인 순위는?", "연령별 소비 패턴 차이는?", "MZ세대 음료 트렌드는?", "온라인 vs 오프라인 구매 행태는?"],
    }

    # ─── 헤더 ───
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        status = "✅ 분석 완료" if st.session_state.indexed.get(category) else ""
        st.markdown(f"### {icon} {title} {status}")

    # ─── 상단: 업로드 + 요약 ───
    upload_col, summary_col = st.columns([1, 3])

    with upload_col:
        uploaded_file = st.file_uploader(
            f"{title} PDF",
            type=["pdf", "docx", "txt"],
            key=f"upload_{category}",
            label_visibility="collapsed",
        )

        if uploaded_file and not st.session_state.indexed.get(category):
            process_upload(uploaded_file, category)
            st.rerun()

        if st.session_state.indexed.get(category):
            info = st.session_state.file_info[category]
            st.success(f"✅ {info.get('name', 'file')}")
            st.caption(f"📄 {info.get('size', '')}")
            st.caption("벡터화 완료")
            if st.button("🔄 다른 파일", key=f"reset_{category}"):
                st.session_state.indexed[category] = False
                st.session_state.uploads[category] = None
                st.session_state.summaries[category] = ""
                st.session_state.keywords[category] = []
                st.session_state[chat_key] = []
                st.session_state[report_key] = []
                st.session_state.vector_store.clear_collection(category)
                st.rerun()
        else:
            st.info("📄 PDF를 업로드해주세요")

    with summary_col:
        if st.session_state.indexed.get(category):
            # 자동 요약
            st.markdown(f"""
            <div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:10px 14px;">
                <div style="font-weight:700;font-size:12px;color:#0369a1;margin-bottom:4px;">📝 AI 자동 요약</div>
                <div style="font-size:12px;color:#334155;line-height:1.65;">{st.session_state.summaries[category]}</div>
            </div>
            """, unsafe_allow_html=True)

            # 키워드
            kw = st.session_state.keywords[category]
            if kw:
                tag_html = " ".join([f'<span class="keyword-tag">{k}</span>' for k in kw])
                st.markdown(f'<div style="margin-top:8px;">🏷️ <strong style="font-size:11px;">핵심 키워드:</strong> {tag_html}</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:40px 20px;text-align:center;">
                <div style="font-size:30px;margin-bottom:8px;">👈</div>
                <div style="font-size:13px;color:#94a3b8;">PDF를 업로드하면 자동 요약과 챗봇이 활성화됩니다</div>
            </div>
            """, unsafe_allow_html=True)

    # ─── 업로드 안 됐으면 여기서 종료 ───
    if not st.session_state.indexed.get(category):
        # 빈 상태 안내
        st.markdown("---")
        st.markdown("""
        <div style="background:white;border:1px solid #e2e8f0;border-radius:10px;padding:40px;text-align:center;">
            <div style="font-size:48px;margin-bottom:12px;">💬</div>
            <div style="font-size:15px;font-weight:600;color:#475569;margin-bottom:6px;">PDF를 업로드하면 AI 챗봇이 활성화됩니다</div>
            <div style="font-size:12px;color:#94a3b8;">업로드 → 텍스트 추출 → RAG 벡터화 → 챗봇 대화 → 보고서 자동 생성</div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown("---")

    # ─── 토픽 필터 ───
    filter_cols = st.columns([1] + [1] * len(topic_options[category]))
    with filter_cols[0]:
        st.markdown("**🔍 토픽필터:**")
    for i, topic in enumerate(topic_options[category]):
        with filter_cols[i + 1]:
            if st.button(
                topic,
                key=f"filter_{category}_{topic}",
                type="primary" if st.session_state[filter_key] == topic else "secondary",
            ):
                st.session_state[filter_key] = topic
                st.rerun()

    # ─── 분할 화면: 챗봇 | 보고서 ───
    chat_col, report_col = st.columns(2)

    # === LEFT: 챗봇 ===
    with chat_col:
        st.markdown(f'<div class="section-header">💬 {title} 전용 챗봇 <span style="font-size:10px;color:#94a3b8;float:right;">Gemini 2.5 Flash · RAG</span></div>', unsafe_allow_html=True)

        # 챗 히스토리 표시
        chat_container = st.container(height=350)
        with chat_container:
            if not st.session_state[chat_key]:
                st.markdown(f"""
                <div style="background:{color}10;border:1px solid {color}25;border-radius:8px;padding:10px;margin-bottom:8px;">
                    <div style="font-size:11px;color:#475569;line-height:1.6;">
                        {icon} 업로드된 PDF 기반으로 답변합니다.<br/>
                        질문하면 분석 결과가 오른쪽 보고서에 자동 추가됩니다.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            for msg in st.session_state[chat_key]:
                render_chat_bubble(msg["role"], msg["content"])

        # 추천 질문
        suggest_cols = st.columns(2)
        for i, q in enumerate(suggest_questions[category]):
            with suggest_cols[i % 2]:
                if st.button(f"💡 {q}", key=f"suggest_{category}_{i}"):
                    handle_chat(q, category, st.session_state[filter_key])
                    st.rerun()

        # 입력
        user_input = st.chat_input(
            f"질문하면 보고서에 자동 반영됩니다...",
            key=f"input_{category}",
        )
        if user_input:
            handle_chat(user_input, category, st.session_state[filter_key])
            st.rerun()

    # === RIGHT: 실시간 보고서 ===
    with report_col:
        st.markdown(f'<div style="background:{color};color:white;padding:6px 12px;border-radius:7px 7px 0 0;font-weight:700;font-size:13px;">📋 실시간 보고서 <span style="font-size:10px;opacity:0.7;float:right;">{len(st.session_state[report_key])}개 섹션</span></div>', unsafe_allow_html=True)

        report_container = st.container(height=350)
        with report_container:
            # 보고서 제목
            st.markdown(f"""
            <div style="text-align:center;margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid {color};">
                <div style="font-size:14px;font-weight:800;color:#1e293b;">{icon} {title} 보고서</div>
                <div style="font-size:10px;color:#64748b;margin-top:3px;">Gemini 2.5 Flash RAG | {time.strftime('%Y.%m.%d')}</div>
            </div>
            """, unsafe_allow_html=True)

            if not st.session_state[report_key]:
                st.info("💬 왼쪽 챗봇에서 질문하면 보고서 섹션이 여기에 추가됩니다.")
            else:
                for section in st.session_state[report_key]:
                    render_report_section(section)

        # 버튼
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("📥 PDF 다운로드", key=f"pdf_{category}", use_container_width=True):
                if st.session_state[report_key]:
                    pdf_bytes = generate_pdf_report(
                        f"{title} 보고서",
                        st.session_state[report_key],
                    )
                    st.download_button(
                        "📥 PDF 저장",
                        data=pdf_bytes,
                        file_name=f"{title}_보고서.pdf",
                        mime="application/pdf",
                        key=f"dl_pdf_{category}",
                    )
                else:
                    st.warning("보고서 섹션이 없습니다.")

        with btn_col2:
            if st.button("📋 통합 보고서로 보내기", key=f"send_{category}", use_container_width=True):
                for section in st.session_state[report_key]:
                    # 이미 통합에 있는지 체크
                    existing_nums = [s["number"] for s in st.session_state.report_integrated]
                    if section["number"] not in existing_nums:
                        st.session_state.report_integrated.append(section.copy())
                st.success("✅ 통합 보고서에 추가됨")


# ============================================================
# 🧪 FORMULA PAGE
# ============================================================
def page_formula():
    if not check_api():
        return

    st.markdown("### 🧪 음료 DB & 배합비 설계")

    # ─── 상단: DB 업로드 + 정보 ───
    db_col, info_col = st.columns([1, 3])

    with db_col:
        db_file = st.file_uploader(
            "음료 DB (xlsx)",
            type=["xlsx", "xls"],
            key="upload_formula_db",
            label_visibility="collapsed",
        )
        if db_file and not st.session_state.beverage_db_loaded:
            with st.spinner("📊 음료 DB 로딩 중..."):
                file_bytes = db_file.read()
                st.session_state.beverage_db = load_beverage_db(file_bytes)
                # DB를 RAG용 텍스트로 변환 후 벡터화
                db_text = beverage_db_to_text(st.session_state.beverage_db)
                chunks = chunk_text(db_text, chunk_size=500, overlap=50)
                for c in chunks:
                    c["category"] = "formula"
                    c["topics"] = ["원료DB"]
                vs = st.session_state.vector_store
                vs.clear_collection("formula")
                vs.add_chunks("formula", chunks)
                st.session_state.beverage_db_loaded = True
            st.rerun()

        if st.session_state.beverage_db_loaded:
            st.success("✅ DB 연결됨")
            if st.button("🔄 DB 교체", key="reset_formula_db"):
                st.session_state.beverage_db_loaded = False
                st.session_state.beverage_db = None
                st.rerun()
        else:
            st.info("📊 음료 DB xlsx를 업로드해주세요")

    with info_col:
        if st.session_state.beverage_db_loaded and st.session_state.beverage_db:
            db = st.session_state.beverage_db
            sheet_info = []
            for name, df in db.items():
                sheet_info.append(f"**{name}**: {len(df)}건")
            st.markdown(f"""
            <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;padding:12px;">
                <div style="font-weight:700;font-size:12px;color:#166534;margin-bottom:6px;">✅ 음료개발 데이터베이스 연결됨</div>
                <div style="font-size:11px;color:#334155;">{' · '.join(sheet_info)}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("음료개발_데이터베이스_v4-1.xlsx를 업로드하면 배합비 설계가 가능합니다.")

    if not st.session_state.beverage_db_loaded:
        return

    st.markdown("---")

    # ─── 분할: 챗봇 | 배합비 ───
    chat_col, formula_col = st.columns(2)

    with chat_col:
        st.markdown('<div class="section-header">💬 배합 설계 챗봇 <span style="font-size:10px;color:#94a3b8;float:right;">음료DB + 트렌드 RAG</span></div>', unsafe_allow_html=True)

        chat_container = st.container(height=380)
        with chat_container:
            if not st.session_state.chat_formula:
                st.info("🧪 트렌드 기반 배합비를 요청하세요.\n예: '저당 프로바이오틱스 음료 배합비 설계해줘'")
            for msg in st.session_state.chat_formula:
                render_chat_bubble(msg["role"], msg["content"])

        # 추천 질문
        sc1, sc2 = st.columns(2)
        with sc1:
            if st.button("💡 저당 프로바이오틱스 배합비", key="sug_f1"):
                # 트렌드 컬렉션도 함께 검색
                extra = [c for c in ["macro", "beverage", "consumer"] if st.session_state.indexed.get(c)]
                handle_chat("트렌드 분석 결과를 반영해서 저당 프로바이오틱스 음료 배합비를 설계해줘", "formula", extra_collections=extra)
                st.rerun()
        with sc2:
            if st.button("💡 제로칼로리 비타민워터", key="sug_f2"):
                extra = [c for c in ["macro", "beverage", "consumer"] if st.session_state.indexed.get(c)]
                handle_chat("제로칼로리 비타민워터 배합비를 설계해줘", "formula", extra_collections=extra)
                st.rerun()

        user_input = st.chat_input("배합비 수정 요청...", key="input_formula")
        if user_input:
            extra = [c for c in ["macro", "beverage", "consumer"] if st.session_state.indexed.get(c)]
            handle_chat(user_input, "formula", extra_collections=extra)
            st.rerun()

    with formula_col:
        st.markdown('<div class="section-header-purple">🧪 배합비 (실시간)</div>', unsafe_allow_html=True)

        formula_container = st.container(height=380)
        with formula_container:
            if st.session_state.report_formula:
                for section in st.session_state.report_formula:
                    render_report_section(section)
            else:
                st.info("💬 왼쪽에서 배합비를 요청하면 여기에 표시됩니다.")

        btn1, btn2 = st.columns(2)
        with btn1:
            if st.button("📥 PDF 다운로드", key="pdf_formula", use_container_width=True):
                if st.session_state.report_formula:
                    pdf_bytes = generate_pdf_report(
                        "배합비 설계 보고서",
                        st.session_state.report_formula,
                    )
                    st.download_button(
                        "📥 저장", data=pdf_bytes,
                        file_name="배합비_보고서.pdf",
                        mime="application/pdf",
                        key="dl_pdf_formula",
                    )
        with btn2:
            if st.button("📋 통합에 추가", key="send_formula", use_container_width=True):
                for s in st.session_state.report_formula:
                    existing_nums = [x["number"] for x in st.session_state.report_integrated]
                    if s["number"] not in existing_nums:
                        st.session_state.report_integrated.append(s.copy())
                st.success("✅ 추가됨")


# ============================================================
# 📋 INTEGRATED REPORT PAGE
# ============================================================
def page_report():
    if not check_api():
        return

    st.markdown("### 📋 통합 분석 보고서")

    # 소스 현황
    sources = []
    for cat, label in [("macro", "거시시장"), ("beverage", "음료시장"), ("consumer", "소비자태도")]:
        if st.session_state.indexed.get(cat):
            sources.append(f"✅ {label}")
        else:
            sources.append(f"⬜ {label}")
    if st.session_state.beverage_db_loaded:
        sources.append("✅ 음료DB")
    else:
        sources.append("⬜ 음료DB")

    st.markdown(f"**소스 현황:** {' · '.join(sources)}")
    st.markdown("---")

    # ─── 분할: 챗봇 | 보고서 ───
    chat_col, report_col = st.columns(2)

    with chat_col:
        st.markdown('<div class="section-header">💬 통합 분석 챗봇</div>', unsafe_allow_html=True)

        chat_container = st.container(height=400)
        with chat_container:
            if not st.session_state.chat_report:
                st.info("🔗 3개 보고서 + 음료 DB를 교차 분석합니다.\n예: '핵심 기회 영역을 도출해줘'")
            for msg in st.session_state.chat_report:
                render_chat_bubble(msg["role"], msg["content"])

        # 추천 질문
        sc1, sc2 = st.columns(2)
        with sc1:
            if st.button("💡 핵심 기회 영역 도출", key="sug_r1"):
                # 통합 분석은 모든 컬렉션 검색
                all_cols = [c for c in ["macro", "beverage", "consumer", "formula"] if st.session_state.indexed.get(c) or (c == "formula" and st.session_state.beverage_db_loaded)]
                handle_chat("3개 트렌드 보고서를 종합해서 핵심 기회 영역을 도출해줘", "report", extra_collections=all_cols)
                st.rerun()
        with sc2:
            if st.button("💡 트렌드→배합비 연결", key="sug_r2"):
                all_cols = [c for c in ["macro", "beverage", "consumer", "formula"] if st.session_state.indexed.get(c) or (c == "formula" and st.session_state.beverage_db_loaded)]
                handle_chat("1순위 기회 영역에 대해 트렌드 근거부터 배합비까지 완성해줘", "report", extra_collections=all_cols)
                st.rerun()

        user_input = st.chat_input("통합 분석 질문...", key="input_report")
        if user_input:
            all_cols = [c for c in ["macro", "beverage", "consumer", "formula"] if st.session_state.indexed.get(c) or (c == "formula" and st.session_state.beverage_db_loaded)]
            handle_chat(user_input, "report", extra_collections=all_cols)
            st.rerun()

    with report_col:
        st.markdown(f'<div class="section-header-purple">📋 통합 보고서 <span style="font-size:10px;opacity:0.7;float:right;">{len(st.session_state.report_integrated)}개 섹션</span></div>', unsafe_allow_html=True)

        report_container = st.container(height=400)
        with report_container:
            st.markdown(f"""
            <div style="text-align:center;margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid #7c3aed;">
                <div style="font-size:15px;font-weight:800;color:#1e293b;">2025 음료 트렌드 & 제품 설계 보고서</div>
                <div style="font-size:10px;color:#64748b;margin-top:3px;">거시 × 음료 × 소비자 × 배합 통합 분석 | {time.strftime('%Y.%m.%d')}</div>
            </div>
            """, unsafe_allow_html=True)

            report_from_chat = st.session_state.get("report_report", [])
            integrated = st.session_state.report_integrated
            existing_nums = [x["number"] for x in integrated]
            all_sections = integrated + [
                s for s in report_from_chat
                if s["number"] not in existing_nums
            ]

            if not all_sections:
                st.info("📋 각 분석 탭에서 '통합 보고서로 보내기'를 누르거나,\n왼쪽 챗봇에서 통합 분석을 요청하세요.")
            else:
                # 목차
                toc = " / ".join([f"{s['number']}. {s['title']}" for s in all_sections])
                st.caption(f"📑 목차: {toc}")
                for section in all_sections:
                    render_report_section(section)

        # 버튼
        btn1, btn2 = st.columns(2)
        with btn1:
            if st.button("📥 PDF 다운로드", key="pdf_report", use_container_width=True):
                all_report = st.session_state.report_integrated + st.session_state.get("report_report", [])
                if all_report:
                    pdf_bytes = generate_pdf_report(
                        "2025 음료 트렌드 & 제품 설계 통합 보고서",
                        all_report,
                    )
                    st.download_button(
                        "📥 저장", data=pdf_bytes,
                        file_name="통합_분석_보고서.pdf",
                        mime="application/pdf",
                        key="dl_pdf_report",
                    )
                else:
                    st.warning("보고서 섹션이 없습니다.")
        with btn2:
            if st.button("🗑️ 보고서 초기화", key="reset_report", use_container_width=True):
                st.session_state.report_integrated = []
                st.session_state.report_report = []
                st.rerun()


# ============================================================
# 라우팅
# ============================================================
page = st.session_state.current_page

if page == "home":
    page_home()
elif page == "macro":
    page_analysis("macro", "거시시장 분석", "📊", "#2563eb")
elif page == "beverage":
    page_analysis("beverage", "음료시장 분석", "🥤", "#059669")
elif page == "consumer":
    page_analysis("consumer", "소비자 태도 분석", "👥", "#d97706")
elif page == "formula":
    page_formula()
elif page == "report":
    page_report()
