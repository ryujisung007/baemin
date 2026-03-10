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

# [시니어 팁] 실행 환경에서 브라우저를 자동 설치하는 견고한 로직
def install_playwright_browsers():
    try:
        # 브라우저 설치 여부 확인 후 설치
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.sidebar.error(f"브라우저 설치 시도 중 오류: {e}")

# 페이지 설정
st.set_page_config(page_title="음료 R&D 트렌드 분석", layout="wide")

# UI 스타일링
st.markdown("""
    <style>
    .stButton>button { background-color: #007BFF; color: white; font-weight: bold; border-radius: 8px; height: 3em; }
    .report-area { padding: 20px; background-color: #f8f9fa; border-radius: 10px; border: 1px solid #dee2e6; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥤 음료 R&D 트렌드 분석 및 배합비 생성기")
st.sidebar.header("⚙️ 환경 설정")

api_key = st.sidebar.text_input("OpenAI API Key", type="password")
client = OpenAI(api_key=api_key) if api_key else None

async def get_trends():
    install_playwright_browsers() # 크롤링 전 브라우저 설치 보장
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://ceo.baemin.com/knowhow/articles?category=102", wait_until="networkidle", timeout=60000)
            titles = await page.locator("h3").all_inner_texts()
            await browser.close()
            
            keywords = ["음료", "카페", "커피", "티", "에이드", "과일", "건강", "저당", "제로", "식물성"]
            return [t.strip() for t in titles if any(k in t for k in keywords)]
        except Exception as e:
            st.warning(f"실시간 데이터 수집 지연으로 기본 데이터를 활용합니다.")
            return ["2026 웰니스 저당 음료", "식물성 대체유 음료", "기능성 과일 에이드"]

def generate_rnd_report(trends):
    prompt = f"당신은 20년 경력의 식품기술사입니다. 트렌드 {trends}를 반영한 신제품 배합비와 전략을 작성하세요. 반드시 표 형식(|원료명|배합비(%)|사용 목적|비고|)을 포함하세요."
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "식품 연구 전문가 모드"}, {"role": "user", "content": prompt}],
            temperature=0.3
        )
        report = res.choices[0].message.content
        
        # 표 추출 로직
        df = pd.DataFrame()
        match = re.search(r'\|.*\|(?:\n\|.*\|)*', report)
        if match:
            lines = match.group(0).strip().split('\n')
            headers = [c.strip() for c in lines[0].split('|')[1:-1]]
            data = [[c.strip() for c in l.split('|')[1:-1]] for l in lines[2:]]
            df = pd.DataFrame(data, columns=headers)
        return report, df
    except Exception as e:
        return f"AI 분석 오류: {e}", pd.DataFrame()

# 메인 실행 버튼
if st.button("🚀 분석 실행 및 엑셀 생성"):
    if not api_key:
        st.error("API Key를 입력해주세요.")
    else:
        with st.status("🏗️ 시스템 준비 및 분석 중...", expanded=True) as s:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            trends = loop.run_until_complete(get_trends())
            report, df = generate_rnd_report(trends)
            s.update(label="✅ 분석 완료", state="complete")

        c1, c2 = st.columns([3, 2])
        with c1:
            st.subheader("📋 R&D 분석 리포트")
            st.markdown(f"<div class='report-area'>{report}</div>", unsafe_allow_html=True)
        with c2:
            if not df.empty:
                st.subheader("📊 설계 배합비")
                st.dataframe(df, use_container_width=True)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='배합비')
                st.download_button("📥 엑셀 다운로드", data=output.getvalue(), file_name="Formulation.xlsx")
