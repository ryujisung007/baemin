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

# [시니어 팁] 브라우저 설치 에러 방지용 자동 설치 로직
def ensure_browsers():
    try:
        # 실행 파일 존재 여부와 상관없이 설치 명령 수행 (이미 있으면 스킵됨)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.sidebar.error(f"브라우저 환경 준비 중: {e}")

# 페이지 설정
st.set_page_config(page_title="음료 R&D AI 시스템", layout="wide")

# UI 스타일링
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

async def scrape_baemin_trends():
    ensure_browsers() # 크롤링 전 브라우저 환경 강제 확보
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await page.goto("https://ceo.baemin.com/knowhow/articles?category=102", wait_until="networkidle", timeout=60000)
            titles = await page.locator("h3").all_inner_texts()
            await browser.close()
            
            keywords = ["음료", "카페", "커피", "티", "에이드", "과일", "저당", "제로", "식물성"]
            return [t.strip() for t in titles if any(k in t for k in keywords)]
        except Exception as e:
            st.warning(f"실시간 수집에 제한이 있어 기본 트렌드를 사용합니다. ({e})")
            return ["2026 웰니스 저당 음료", "식물성 대체유 음료", "기능성 블렌딩 티"]

def generate_rnd_data(trends):
    prompt = f"당신은 20년 경력의 식품기술사입니다. {trends} 트렌드를 기반으로 배합비와 전략을 작성하세요. 반드시 마크다운 표 형식(|원료명|배합비(%)|사용 목적|비고|)을 포함하세요."
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "식품 R&D 전문가"}, {"role": "user", "content": prompt}],
            temperature=0.4
        )
        report = res.choices[0].message.content
        table_pattern = re.compile(r'\|.*\|(?:\n\|.*\|)*')
        match = table_pattern.search(report)
        df = pd.DataFrame()
        if match:
            lines = match.group(0).strip().split('\n')
            headers = [c.strip() for c in lines[0].split('|')[1:-1]]
            data = [[c.strip() for c in l.split('|')[1:-1]] for l in lines[2:]]
            df = pd.DataFrame(data, columns=headers)
        return report, df
    except Exception as e:
        return f"분석 실패: {e}", pd.DataFrame()

if st.button("🚀 분석 시작"):
    if not api_key:
        st.warning("사이드바에 API Key를 넣어주세요.")
    else:
        with st.status("🛠️ 시스템 가동 중...", expanded=True) as status:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            trends = loop.run_until_complete(scrape_baemin_trends())
            report, df = generate_rnd_data(trends)
            status.update(label="✅ 완료!", state="complete", expanded=False)

        c1, c2 = st.columns([3, 2])
        with c1:
            st.subheader("📋 R&D 분석 리포트")
            st.markdown(f"<div class='report-box'>{report}</div>", unsafe_allow_html=True)
        with c2:
            if not df.empty:
                st.subheader("📊 설계 배합비")
                st.dataframe(df, use_container_width=True)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='배합비')
                st.download_button("📥 엑셀 다운로드", data=output.getvalue(), file_name="R&D_Result.xlsx")
