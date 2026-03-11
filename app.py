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
# 1. 시스템 설정
# ==========================================
st.set_page_config(page_title="음료 R&D 실시간 대시보드", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #007BFF; color: white; font-weight: bold; }
    .status-log { padding: 10px; background-color: #f0f2f6; border-radius: 5px; font-family: 'Courier New', Courier, monospace; font-size: 0.9em; }
    .data-card { padding: 15px; border: 1px solid #e6e9ef; border-radius: 10px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥤 실시간 음료 R&D 데이터 가공 대시보드")
st.sidebar.header("⚙️ API 설정")

api_key = st.sidebar.text_input("OpenAI API Key", type="password")
client = OpenAI(api_key=api_key) if api_key else None

def ensure_playwright():
    """런타임 브라우저 설치 보장"""
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.sidebar.error(f"설치 알림: {e}")

# ==========================================
# 2. 실시간 데이터 파이프라인 시각화
# ==========================================
async def run_data_pipeline(log_placeholder):
    ensure_playwright()
    
    log_placeholder.markdown("🔍 **[1/4]** 시스템 라이브러리 확인 및 브라우저 초기화 중...")
    
    async with async_playwright() as p:
        try:
            # 시니어 팁: 리눅스 환경 에러 방지를 위한 핵심 인자 추가
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            context = await browser.new_context(user_agent="Mozilla/5.0")
            page = await context.new_page()
            
            url = "https://ceo.baemin.com/knowhow/articles?category=102"
            log_placeholder.markdown(f"🌐 **[2/4]** 타겟 데이터 소스 접속: `{url}`")
            
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            log_placeholder.markdown("📂 **[3/4]** 비정형 텍스트 수집 및 파싱 중...")
            raw_titles = await page.locator("h3").all_inner_texts()
            await browser.close()
            
            log_placeholder.markdown(f"✅ **[4/4]** 수집 완료! (총 {len(raw_titles)}건 확보)")
            
            keywords = ["음료", "카페", "커피", "티", "에이드", "과일", "저당", "제로", "식물성"]
            filtered = [t.strip() for t in raw_titles if any(k in t for k in keywords)]
            
            return raw_titles, filtered
        except Exception as e:
            log_placeholder.error(f"❌ 파이프라인 중단: {str(e)}")
            return [], []

# ==========================================
# 3. 메인 대시보드 가동
# ==========================================
if st.button("🚀 R&D 데이터 파이프라인 가동"):
    if not api_key:
        st.error("API Key를 입력해 주세요.")
    else:
        # 대시보드 탭 구성
        t_ingest, t_analyze, t_export = st.tabs(["📡 데이터 인입", "🧠 AI 가공 논리", "📊 최종 자산"])
        
        with t_ingest:
            st.subheader("Raw Data Stream")
            log_area = st.empty()
            raw, filtered = asyncio.run(run_data_pipeline(log_area))
            
            c1, c2 = st.columns(2)
            with c1:
                st.write("**[원본 데이터 스트림]**")
                st.write(raw if raw else "데이터 없음")
            with c2:
                st.write("**[필터링된 트렌드 시그널]**")
                st.success(filtered if filtered else "필터링된 신호 없음")

        with t_analyze:
            st.subheader("AI R&D Processing")
            if filtered:
                with st.status("식품기술사 AI가 배합비를 산출하고 있습니다...") as s:
                    st.write("- 트렌드 시그널 분석 중...")
                    st.write("- 식품공전 기준 성분 검토 중...")
                    st.write("- 최적 배합비 표 생성 중...")
                    
                    prompt = f"20년 차 식품기술사로서 {filtered} 트렌드 기반 음료 배합비를 표 형식(|원료명|배합비(%)|사용 목적|비고|)으로 상세히 작성하세요."
                    res = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3
                    )
                    report = res.choices[0].message.content
                    s.update(label="분석 완료", state="complete")
                
                st.markdown(report)
            else:
                st.warning("분석할 트렌드 데이터가 수집되지 않았습니다.")

        with t_export:
            st.subheader("Final R&D Assets")
            if 'report' in locals():
                # 표 파싱 및 데이터프레임 변환
                match = re.search(r'\|.*\|(?:\n\|.*\|)*', report)
                if match:
                    lines = match.group(0).strip().split('\n')
                    headers = [c.strip() for c in lines[0].split('|')[1:-1]]
                    data = [[c.strip() for c in l.split('|')[1:-1]] for l in lines[2:]]
                    df = pd.DataFrame(data, columns=headers)
                    
                    st.dataframe(df, use_container_width=True)
                    
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='Formulation')
                    st.download_button("📥 배합비 엑셀 저장", data=output.getvalue(), file_name="R&D_Result.xlsx")

st.sidebar.divider()
st.sidebar.caption("Pipeline: Playwright Headless -> Regex Parsing -> GPT-4o-mini")
