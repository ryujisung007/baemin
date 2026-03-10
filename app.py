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
st.set_page_config(
    page_title="음료 R&D 트렌드 분석 시스템",
    page_icon="🥤",
    layout="wide"
)

# UI 스타일 커스텀 (시니어의 꼼꼼한 가독성 설계)
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #007BFF; color: white; font-weight: bold; }
    .report-box { padding: 20px; border-radius: 10px; background-color: #f1f3f5; border: 1px solid #dee2e6; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥤 음료 R&D 트렌드 분석 및 엑셀 배합비 생성기")
st.sidebar.header("⚙️ 환경 설정")

# OpenAI 클라이언트 설정
api_key = st.sidebar.text_input("OpenAI API Key", type="password", help="GPT-4o-mini 모델 사용을 위해 필요합니다.")
client = OpenAI(api_key=api_key) if api_key else None

# ==========================================
# 2. 브라우저 자동 설치 로직 (중요: 에러 방지용)
# ==========================================
def install_playwright():
    """브라우저가 없는 환경에서 자동으로 설치를 시도합니다."""
    try:
        # 이미 설치되어 있는지 확인하는 과정을 생략하고 안전하게 install 실행
        # 로컬 환경이나 서버 환경에서 모두 작동하도록 설계
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.sidebar.error(f"브라우저 설치 시도 중 알림: {e}")

# ==========================================
# 3. 크롤링 엔진 (Playwright)
# ==========================================
async def scrape_baemin_trends():
    """배민외식업광장에서 비정형 트렌드 데이터를 수집합니다."""
    # 실행 전 브라우저 설치 확인
    install_playwright()
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # 트렌드 페이지 이동
            await page.goto("https://ceo.baemin.com/knowhow/articles?category=102", wait_until="networkidle", timeout=60000)
            
            # 아티클 제목 수집 (시니어의 유연한 셀렉터 설계)
            titles = await page.locator("h3").all_inner_texts()
            await browser.close()
            
            # 음료 관련 필터링
            drink_keywords = ["음료", "카페", "커피", "티", "에이드", "과일", "저당", "제로", "식물성", "디저트", "건강"]
            return [t.strip() for t in titles if any(k in t for k in drink_keywords)]
        except Exception as e:
            st.error(f"데이터 수집 중 오류 발생: {e}")
            return []

# ==========================================
# 4. AI 분석 및 데이터 구조화
# ==========================================
def generate_formula_and_df(trends):
    """트렌드 분석 후 배합비 표를 추출하여 데이터프레임으로 변환합니다."""
    prompt = f"""
    당신은 20년 경력의 식품기술사입니다. 다음 트렌드({trends})를 기반으로 음료 신제품 배합비를 설계하세요.

    [작성 가이드]
    1. 제품 컨셉: 타겟 소비자와 시장성 요약.
    2. 배합비 설계: 반드시 아래의 Markdown 표 형식을 엄수할 것 (엑셀 변환용).
       | 원료명 | 배합비(%) | 사용 목적 | 비고 |
       | :--- | :--- | :--- | :--- |
    3. 상세 가이드: 용도, 용법, 사용주의사항(보관 및 법적 규정).
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "당신은 꼼꼼하고 논리적인 식품 R&D 전문가입니다."},
                      {"role": "user", "content": prompt}],
            temperature=0.4
        )
        report = response.choices[0].message.content
        
        # 정규표현식으로 표 데이터만 파싱하여 DataFrame 생성
        table_pattern = re.compile(r'\|.*\|(?:\n\|.*\|)*')
        match = table_pattern.search(report)
        df = pd.DataFrame()
        
        if match:
            table_str = match.group(0)
            lines = table_str.strip().split('\n')
            headers = [c.strip() for c in lines[0].split('|')[1:-1]]
            data_rows = []
            for line in lines[2:]:
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if len(cells) == len(headers):
                    data_rows.append(cells)
            df = pd.DataFrame(data_rows, columns=headers)
            
        return report, df
    except Exception as e:
        return f"AI 분석 실패: {e}", pd.DataFrame()

# ==========================================
# 5. 메인 UI 로직
# ==========================================
st.sidebar.divider()
st.sidebar.caption("Senior AI & Food Tech Solution v1.6")

if st.button("🚀 실시간 트렌드 분석 및 엑셀 배합비 생성"):
    if not api_key:
        st.warning("먼저 사이드바에 OpenAI API Key를 입력해주세요.")
    else:
        with st.status("🔍 시스템 가동 중 (브라우저 확인 및 데이터 수집)...", expanded=True) as status:
            st.write("1. 배달 플랫폼 트렌드 크롤링 시도...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            trends = loop.run_until_complete(scrape_baemin_trends())
            
            # 수집 데이터가 없을 경우를 대비한 폴백 데이터
            if not trends:
                st.write("💡 실시간 수집 실패로 인해 최신 일반 트렌드 데이터를 활용합니다.")
                trends = ["2026 웰니스 저당 음료 트렌드", "식물성 대체유 기반 라떼", "기능성 블렌딩 티"]
                
            st.write(f"2. {len(trends)}개의 시그널 분석 및 배합 설계 진행 중...")
            report_text, formula_df = generate_formula_and_df(trends)
            status.update(label="✅ 분석 및 설계 완료!", state="complete", expanded=False)

        # 결과 출력 레이아웃
        col_res, col_data = st.columns([3, 2])
        
        with col_res:
            st.subheader("📋 식품 R&D 전략 리포트")
            st.markdown(f"<div class='report-box'>{report_text}</div>", unsafe_allow_html=True)
            
        with col_data:
            if not formula_df.empty:
                st.subheader("📊 설계된 배합비 (Excel 데이터)")
                st.dataframe(formula_df, use_container_width=True)
                
                # 엑셀 다운로드 생성
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    formula_df.to_excel(writer, index=False, sheet_name='배합비설계')
                excel_data = output.getvalue()
                
                st.download_button(
                    label="📥 배합비 엑셀(XLSX) 다운로드",
                    data=excel_data,
                    file_name=f"Formulation_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
