import streamlit as st
import asyncio
import pandas as pd
from playwright.async_api import async_playwright
from openai import OpenAI
import datetime
import io
import re

# ==========================================
# 1. 초기 설정 및 시스템 구성
# ==========================================
st.set_page_config(
    page_title="음료 R&D 트렌드 분석 시스템",
    page_icon="🥤",
    layout="wide"
)

# UI 스타일 커스텀
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #007BFF; color: white; font-weight: bold; }
    .report-box { padding: 20px; border-radius: 10px; background-color: #f1f3f5; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥤 음료 R&D 트렌드 분석 및 엑셀 배합비 생성기")
st.sidebar.header("⚙️ 환경 설정")

# API 키 입력
api_key = st.sidebar.text_input("OpenAI API Key", type="password", help="GPT-4o-mini 모델 사용을 위해 필요합니다.")
client = OpenAI(api_key=api_key) if api_key else None

# ==========================================
# 2. 크롤링 엔진 (Playwright)
# ==========================================
async def scrape_baemin_trends():
    """배민외식업광장에서 비정형 트렌드 데이터를 수집합니다."""
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # 트렌드 페이지 이동
            await page.goto("https://ceo.baemin.com/knowhow/articles?category=102", wait_until="networkidle", timeout=60000)
            
            # 아티클 제목 수집
            titles = await page.locator("h3").all_inner_texts()
            await browser.close()
            
            # 음료 관련 필터링
            drink_keywords = ["음료", "카페", "커피", "티", "에이드", "과일", "저당", "제로", "식물성", "디저트", "건강"]
            return [t.strip() for t in titles if any(k in t for k in drink_keywords)]
        except Exception as e:
            st.error(f"데이터 수집 중 오류 발생: {e}")
            return []

# ==========================================
# 3. AI 분석 및 데이터 구조화
# ==========================================
def generate_formula_and_df(trends):
    """트렌드 분석 후 배합비 표를 추출하여 데이터프레임으로 변환합니다."""
    prompt = f"""
    당신은 20년 경력의 식품기술사입니다. 다음 트렌드({trends})를 기반으로 음료 신제품 배합비를 설계하세요.

    [작성 가이드]
    1. 제품 컨셉: 타겟 소비자와 시장성 요약.
    2. 배합비 설계: 반드시 아래의 Markdown 표 형식을 엄수할 것.
       | 원료명 | 배합비(%) | 사용 목적 | 비고 |
       | :--- | :--- | :--- | :--- |
       | ... | ... | ... | ... |
    3. 상세 가이드: 용도, 용법, 사용주의사항(보관 및 법적 규정).
    
    * 배합비는 문헌 근거에 따라 표준적인 수치를 제시할 것.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "당신은 꼼꼼하고 논리적인 식품 R&D 전문가입니다."},
                      {"role": "user", "content": prompt}],
            temperature=0.4
        )
        report = response.choices[0].message.content
        
        # 정규표현식으로 표 데이터만 파싱
        table_pattern = re.compile(r'\|.*\|(?:\n\|.*\|)*')
        match = table_pattern.search(report)
        df = pd.DataFrame()
        
        if match:
            table_str = match.group(0)
            lines = table_str.strip().split('\n')
            # 헤더 추출
            headers = [c.strip() for c in lines[0].split('|')[1:-1]]
            # 데이터 추출 (구분선 제외)
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
# 4. 메인 UI 로직
# ==========================================
st.sidebar.divider()
st.sidebar.caption("Senior Developer & Food Tech specialist")

if st.button("🚀 실시간 트렌드 분석 및 엑셀 배합비 생성"):
    if not api_key:
        st.warning("먼저 사이드바에 OpenAI API Key를 입력해주세요.")
    else:
        # 진행 상태 표시
        with st.status("🔍 데이터 수집 및 분석 진행 중...", expanded=True) as status:
            st.write("1. 배달 플랫폼 트렌드 크롤링 중...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            trends = loop.run_until_complete(scrape_baemin_trends())
            
            if not trends:
                trends = ["최신 제로 슈가 및 기능성 건강 음료"] # 폴백 데이터
                
            st.write(f"2. {len(trends)}개의 키워드 분석 및 배합 설계 중...")
            report_text, formula_df = generate_formula_and_df(trends)
            status.update(label="✅ 분석 완료!", state="complete", expanded=False)

        # 결과 렌더링
        col_res, col_data = st.columns([3, 2])
        
        with col_res:
            st.subheader("📋 식품 R&D 전략 리포트")
            st.markdown(report_text)
            
        with col_data:
            if not formula_df.empty:
                st.subheader("📊 추출된 배합 데이터")
                st.dataframe(formula_df, use_container_width=True)
                
                # 엑셀 다운로드 파일 생성
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    formula_df.to_excel(writer, index=False, sheet_name='Formulation')
                excel_data = output.getvalue()
                
                st.download_button(
                    label="📥 배합비 엑셀(XLSX) 다운로드",
                    data=excel_data,
                    file_name=f"Formulation_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
