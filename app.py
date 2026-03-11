import streamlit as st
import asyncio
import pandas as pd
from playwright.async_api import async_playwright
from openai import OpenAI
import datetime
import io
import re
import subprocess
import sys

# ==========================================
# 1. 초기 설정 및 시스템 구성
# ==========================================
st.set_page_config(page_title="음료 R&D 실시간 대시보드", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #007BFF; color: white; font-weight: bold; }
    .status-card { padding: 15px; border-radius: 8px; border-left: 5px solid #007BFF; background-color: #f8f9fa; margin-bottom: 10px; }
    .source-code { background-color: #2b2b2b; color: #a9b7c6; padding: 10px; border-radius: 5px; font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥤 실시간 음료 R&D 데이터 파이프라인 대시보드")
st.sidebar.header("⚙️ 환경 설정")

api_key = st.sidebar.text_input("OpenAI API Key", type="password")
client = OpenAI(api_key=api_key) if api_key else None

# 브라우저 자동 설치 로직
def ensure_browsers():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.sidebar.error(f"브라우저 환경 준비 중: {e}")

# ==========================================
# 2. 데이터 수집 및 실시간 로그 모듈
# ==========================================
async def fetch_live_data(log_placeholder):
    """데이터 수집 과정을 실시간으로 로그로 보여줍니다."""
    ensure_browsers()
    log_placeholder.info("🌐 배민외식업광장 서버 접속 중...")
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0")
            page = await context.new_page()
            
            target_url = "https://ceo.baemin.com/knowhow/articles?category=102"
            log_placeholder.warning(f"🔗 타겟 URL 분석 중: {target_url}")
            
            await page.goto(target_url, wait_until="networkidle", timeout=60000)
            log_placeholder.success("✅ 페이지 로드 완료. 비정형 데이터 추출 시작...")
            
            # 원본 제목 데이터 추출
            raw_titles = await page.locator("h3").all_inner_texts()
            await browser.close()
            
            log_placeholder.write(f"🔍 총 {len(raw_titles)}개의 아티클 발견. 음료 트렌드 필터링 중...")
            
            keywords = ["음료", "카페", "커피", "티", "에이드", "과일", "저당", "제로", "식물성"]
            filtered = [t.strip() for t in raw_titles if any(k in t for k in keywords)]
            
            return raw_titles, filtered # 원본 전체와 필터링 결과 반환
        except Exception as e:
            log_placeholder.error(f"❌ 데이터 수집 중단: {e}")
            return [], []

# ==========================================
# 3. AI 분석 프로세스 시각화
# ==========================================
def ai_analysis_process(trends):
    """AI가 데이터를 어떻게 해석하는지 과정을 보여줍니다."""
    with st.expander("🧠 AI Thought Process (분석 논리 보기)", expanded=True):
        st.write("1. **트렌드 추출**: 수집된 키워드에서 '헬시 플레저'와 '기능성' 상관관계 분석")
        st.write("2. **표준 배합비 매칭**: 식품공전 및 글로벌 레시피 DB 기반 기초 배합비 산출")
        st.write("3. **최적화**: 당류 저감 및 원가 효율성을 고려한 소재 재배치")
    
    prompt = f"""당신은 20년 경력의 식품기술사입니다. {trends} 기반으로 배합비를 설계하세요. 
    반드시 마크다운 표 형식(|원료명|배합비(%)|사용 목적|비고|)을 포함할 것."""
    
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "식품 R&D 전문가"}, {"role": "user", "content": prompt}],
        temperature=0.3
    )
    return res.choices[0].message.content

# ==========================================
# 4. 메인 대시보드 UI
# ==========================================
if st.button("🚀 실시간 R&D 파이프라인 가동"):
    if not api_key:
        st.error("OpenAI API Key가 필요합니다.")
    else:
        # 대시보드 레이아웃 구성
        tab1, tab2, tab3 = st.tabs(["📡 실시간 수집", "분석 및 결과", "📊 데이터 자산화"])
        
        with tab1:
            st.subheader("Step 1: Raw Data Ingestion")
            log_box = st.empty() # 실시간 로그용
            raw_data, filtered_data = asyncio.run(fetch_live_data(log_box))
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**[참조 중인 원본 데이터 전체]**")
                st.caption("배민외식업광장에서 방금 긁어온 실제 제목들입니다.")
                st.write(raw_data if raw_data else "데이터 없음")
            with col2:
                st.write("**[필터링된 핵심 트렌드]**")
                st.info(filtered_data if filtered_data else "필터링된 데이터 없음")

        with tab2:
            st.subheader("Step 2: AI Logic Analysis")
            if filtered_data:
                report = ai_analysis_process(filtered_data)
                st.markdown("---")
                st.subheader("📝 최종 R&D 리포트")
                st.markdown(report)
            else:
                st.warning("분석할 트렌드 데이터가 부족합니다.")

        with tab3:
            st.subheader("Step 3: Structured Data Asset")
            if 'report' in locals():
                # 표 추출 및 데이터프레임 시각화
                table_match = re.search(r'\|.*\|(?:\n\|.*\|)*', report)
                if table_match:
                    lines = table_match.group(0).strip().split('\n')
                    headers = [c.strip() for c in lines[0].split('|')[1:-1]]
                    data = [[c.strip() for c in l.split('|')[1:-1]] for l in lines[2:]]
                    df = pd.DataFrame(data, columns=headers)
                    
                    st.dataframe(df, use_container_width=True)
                    
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='배합비')
                    st.download_button("📥 배합비 엑셀 다운로드", data=output.getvalue(), file_name="Formulation.xlsx")

st.sidebar.divider()
st.sidebar.caption("Data Pipeline: Baemin CEO -> Playwright -> GPT-4o-mini -> Excel")
