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
import os

# ==========================================
# 1. 초기 설정 및 시스템 구성
# ==========================================
st.set_page_config(
    page_title="음료 R&D 트렌드 분석 시스템",
    page_icon="🥤",
    layout="wide"
)

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #007BFF; color: white; font-weight: bold; }
    .report-box { padding: 20px; border-radius: 10px; background-color: #f1f3f5; border: 1px solid #dee2e6; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥤 음료 R&D 트렌드 분석 및 엑셀 배합비 생성기")
st.sidebar.header("⚙️ 환경 설정")

api_key = st.sidebar.text_input("OpenAI API Key", type="password")
client = OpenAI(api_key=api_key) if api_key else None

# ==========================================
# 2. 서버 환경 대응 브라우저 설치 로직
# ==========================================
def ensure_playwright_browsers():
    """브라우저 미설치 에러를 방지하기 위해 실행 시점에 체크 및 설치"""
    try:
        # 브라우저가 설치되는 경로 확인 (기본 경로 체크)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.error(f"브라우저 설치 중 오류가 발생했습니다: {e}")

# ==========================================
# 3. 크롤링 엔진 (Playwright)
# ==========================================
async def scrape_baemin_trends():
    """배민외식업광장에서 트렌드 데이터를 수집합니다."""
    # 실행 시점에 브라우저 설치 보장
    ensure_playwright_browsers()
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # 페이지 이동 및 대기
            await page.goto("https://ceo.baemin.com/knowhow/articles?category=102", wait_until="networkidle", timeout=60000)
            
            # 제목 추출
            titles = await page.locator("h3").all_inner_texts()
            await browser.close()
            
            keywords = ["음료", "카페", "커피", "티", "에이드", "과일", "저당", "제로", "식물성", "디저트", "건강"]
            filtered = [t.strip() for t in titles if any(k in t for k in keywords)]
            return filtered
        except Exception as e:
            st.warning(f"실시간 수집에 제한이 있어 기본 트렌드 데이터를 활용합니다. (원인: {e})")
            return []

# ==========================================
# 4. AI R&D 분석 모듈
# ==========================================
def generate_formula_and_df(trends):
    """트렌드 기반 배합비 생성 및 표 파싱"""
    if not trends:
        trends = ["2026 웰니스 저당 음료", "식물성 단백질 음료", "기능성 블렌딩 티"]
        
    prompt = f"""
    당신은 20년 경력의 식품기술사입니다. 다음 트렌드({trends})를 기반으로 신제품 배합비를 설계하세요.

    [작성 규칙]
    1. 제품 컨셉 및 전략 요약.
    2. 배합비 설계: 반드시 아래의 Markdown 표 형식을 사용할 것.
       | 원료명 | 배합비(%) | 사용 목적 | 비고 |
       | :--- | :--- | :--- | :--- |
    3. 용도, 용법, 사용주의사항(보관 및 법적 규정) 명시.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "당신은 꼼꼼한 식품 전문가입니다."},
                      {"role": "user", "content": prompt}],
            temperature=0.4
        )
        report = response.choices[0].message.content
        
        # 표 파싱 로직
        table_pattern = re.compile(r'\|.*\|(?:\n\|.*\|)*')
        match = table_pattern.search(report)
        df = pd.DataFrame()
        
        if match:
            lines = match.group(0).strip().split('\n')
            headers = [c.strip() for c in lines[0].split('|')[1:-1]]
            data_rows = [[c.strip() for c in l.split('|')[1:-1]] for l in lines[2:]]
            df = pd.DataFrame(data_rows, columns=headers)
            
        return report, df
    except Exception as e:
        return f"분석 실패: {e}", pd.DataFrame()

# ==========================================
# 5. 메인 실행부
# ==========================================
if st.button("🚀 데이터 수집 및 분석 시작"):
    if not api_key:
        st.warning("사이드바에 OpenAI API Key를 입력해주세요.")
    else:
        with st.status("🛠️ 시스템 가동 중 (브라우저 설치 및 데이터 수집)...", expanded=True) as status:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            trends = loop.run_until_complete(scrape_baemin_trends())
            
            st.write("🤖 AI 배합 설계 및 리포트 작성 중...")
            report_text, formula_df = generate_formula_and_df(trends)
            status.update(label="✅ 분석 완료!", state="complete", expanded=False)

        col1, col2 = st.columns([3, 2])
        with col1:
            st.subheader("📋 R&D 분석 리포트")
            st.markdown(f"<div class='report-box'>{report_text}</div>", unsafe_allow_html=True)
            
        with col2:
            if not formula_df.empty:
                st.subheader("📊 설계된 배합비")
                st.dataframe(formula_df, use_container_width=True)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    formula_df.to_excel(writer, index=False, sheet_name='Formulation')
                
                st.download_button(
                    label="📥 배합비 엑셀 다운로드",
                    data=output.getvalue(),
                    file_name=f"Formulation_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

st.sidebar.divider()
st.sidebar.caption("Senior R&D Assistant v1.7")
