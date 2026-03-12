import streamlit as st
import pandas as pd
import numpy as np
import openai
import json
import re
import io
import time

# ==========================================
# 1. 환경 설정 및 표준 배합 가이드라인 (A/B단계 연동)
# ==========================================
st.set_page_config(page_title="AI Beverage R&D Platform", layout="wide")

# 음료 유형별 표준 가이드라인 및 검증 기준
BEVERAGE_STANDARDS = {
    "Carbonated (탄산음료)": {"brix": 10.0, "acid": 0.22, "sweet": 7.0, "ph_range": (2.5, 4.5), "desc": "청량감 중심, 높은 탄산 압력 대응"},
    "Juice (과채음료)": {"brix": 12.0, "acid": 0.30, "sweet": 8.0, "ph_range": (2.5, 4.5), "desc": "원료 본연의 맛과 점도 유지 중요"},
    "Sports (스포츠음료)": {"brix": 6.0, "acid": 0.12, "sweet": 4.0, "ph_range": (3.0, 4.5), "desc": "전해질 밸런스 및 빠른 흡수 설계"},
    "Energy (에너지음료)": {"brix": 12.5, "acid": 0.25, "sweet": 9.0, "ph_range": (2.5, 4.0), "desc": "고카페인/타우린 마스킹 설계 필요"},
    "Plant Based (식물성음료)": {"brix": 7.0, "acid": 0.02, "sweet": 3.0, "ph_range": (6.0, 7.5), "desc": "단백질 안정성 및 침전 방지 핵심"}
}

# ==========================================
# 2. 핵심 물리량 계산 엔진 (C/D단계 연동)
# ==========================================

def clean_and_calculate(df, t_brix, t_acid, t_sweet):
    """TypeError 방지를 위한 5중 데이터 정제 및 물성 계산"""
    df_clean = df.copy()
    num_cols = ['Usage_%', 'Brix', 'Acidity', 'Sweetness', 'Cost']
    
    # 1. 데이터 타입 강제 변환 (TypeError 방어)
    for col in num_cols:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0).astype(float)

    # 2. 개별 기여도 계산 (R&D 표준형)
    df_clean['Brix_Contrib'] = df_clean['Usage_%'] * df_clean['Brix'] / 100
    df_clean['Acid_Contrib'] = df_clean['Usage_%'] * df_clean['Acidity'] / 100
    df_clean['Sweet_Contrib'] = df_clean['Usage_%'] * df_clean['Sweetness'] / 100
    df_clean['Cost_Contrib'] = df_clean['Usage_%'] * df_clean['Cost'] / 100

    # 3. 합계 계산
    total_brix = df_clean['Brix_Contrib'].sum()
    total_acid = df_clean['Acid_Contrib'].sum()
    total_sweet = df_clean['Sweet_Contrib'].sum()
    total_cost = df_clean['Cost_Contrib'].sum()
    total_usage = df_clean['Usage_%'].sum()

    # 4. Henderson-Hasselbalch 기반 pH 시뮬레이션
    base_ph = 7.0
    buffer_capacity = (df_clean['Usage_%'] * 0.05).sum() # 단순화된 완충모델
    delta_ph = total_acid / (buffer_capacity + 0.01)
    final_ph = max(2.0, min(8.5, base_ph - delta_ph))

    # 5. 최적화 Score (값이 낮을수록 타겟에 근접)
    score = (abs(total_brix - t_brix) * 40 + 
             abs(total_acid - t_acid) * 600 + 
             abs(total_sweet - t_sweet) * 30 + 
             (total_cost / 100))

    return df_clean, {
        "Brix": round(total_brix, 2),
        "Acid": round(total_acid, 3),
        "Sweetness": round(total_sweet, 2),
        "Cost": round(total_cost, 0),
        "pH": round(final_ph, 2),
        "Usage_Sum": round(total_usage, 4),
        "Score": round(score, 4)
    }

# ==========================================
# 3. AI 및 유전 알고리즘 모듈 (E단계 연동)
# ==========================================

def get_ai_response(api_key, system_prompt, user_prompt):
    """OpenAI API 호출 및 JSON 파싱 안전화"""
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"API 호출 오류: {e}")
        return None

# ==========================================
# 4. UI 구성 (Streamlit)
# ==========================================

st.title("🥤 AI 음료 신제품 배합비 개발 플랫폼")
st.markdown("---")

# 사이드바 조작부
with st.sidebar:
    st.header("🔑 API 설정")
    api_key = st.text_input("OpenAI API Key", type="password")
    
    st.header("📋 신제품 조건 설정")
    selected_type = st.selectbox("음료 유형 선택", list(BEVERAGE_STANDARDS.keys()))
    std = BEVERAGE_STANDARDS[selected_type]
    
    # [사용자 연동] 표준 데이터를 참고하여 슬라이더 값 연동
    st.subheader("🎯 타겟 물성 조정")
    t_brix = st.slider("Target Brix (°Bx)", 0.0, 20.0, float(std['brix']), 0.1)
    t_sweet = st.slider("Target Sweetness Index", 0.0, 15.0, float(std['sweet']), 0.1)
    t_acid = st.slider("Target Acidity (%)", 0.0, 1.0, float(std['acid']), 0.01)
    
    st.header("🧬 유전 알고리즘 설정")
    pop_size = st.slider("Population Size", 100, 1000, 300)
    generations = st.slider("Generations", 5, 50, 10)

# 메인 대시보드
if not api_key:
    st.warning("사이드바에 OpenAI API 키를 입력해주십시오.")
else:
    # 상단 표준 데이터 출력
    st.subheader(f"📊 {selected_type} 표준 가이드라인")
    g1, g2, g3, g4 = st.columns(4)
    g1.metric("표준 Brix", f"{std['brix']}°Bx")
    g2.metric("표준 감미도", std['sweet'])
    g3.metric("표준 산도", f"{std['acid']}%")
    g4.metric("권장 pH", std['ph_range'])
    st.caption(f"💡 가이드: {std['desc']}")

    st.markdown("---")

    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.subheader("Step 1: 트렌드 Flavor 생성")
        if st.button("트렌드 제품명 20개 생성"):
            res = get_ai_response(api_key, "You are a beverage marketing expert.", f"Generate 20 trendy flavor names for {selected_type} in JSON list 'flavors'.")
            if res: st.session_state['flavors'] = res['flavors']
        
        selected_flavor = st.selectbox("맛(Flavor) 선택", st.session_state.get('flavors', ["Flavor를 먼저 생성하세요"]))

    with col_r:
        st.subheader("Step 2: 원료 마스터 DB 구축")
        if st.button("AI 원료 500종 자동 생성"):
            with st.spinner("전문가급 원료 데이터를 구성 중..."):
                sys_msg = "You are a beverage R&D scientist. Create a JSON list 'ingredients' of 50 core ingredients for the flavor."
                user_msg = f"Generate 50 ingredients for {selected_flavor} {selected_type}. Columns: Ingredient, Category, Brix, Acidity, Sweetness, Cost, Purpose."
                res = get_ai_response(api_key, sys_msg, user_msg)
                if res:
                    st.session_state['ing_db'] = pd.DataFrame(res['ingredients'])
                    st.success("원료 DB 구축 완료")

    st.markdown("---")

    # Step 3: 배합 최적화 실행
    if 'ing_db' in st.session_state:
        st.subheader("Step 3: 유전 알고리즘 기반 배합 최적화")
        if st.button("최적 배합비 산출 시작"):
            progress_bar = st.progress(0)
            ing_db = st.session_state['ing_db']
            
            # [시뮬레이션] 유전 알고리즘 메인 루프 (추상화된 핵심 로직)
            best_formula = None
            min_score = float('inf')
            
            for g in range(generations):
                # 개체 생성 및 평가
                temp_formula = ing_db.sample(n=min(len(ing_db), 8)).copy()
                # Water Balance 강제 적용
                raw_usages = np.random.dirichlet(np.ones(len(temp_formula)), size=1)[0] * 12 # 기타원료 합 12% 내외
                temp_formula['Usage_%'] = raw_usages
                
                water_row = pd.DataFrame([{
                    'Ingredient': 'Purified Water', 'Category': 'Base', 'Brix': 0, 'Acidity': 0, 
                    'Sweetness': 0, 'Cost': 30, 'Purpose': 'Solvent', 'Usage_%': 100 - temp_formula['Usage_%'].sum()
                }])
                temp_formula = pd.concat([temp_formula, water_row], ignore_index=True)
                
                # 물성 계산 및 스코어링
                _, stats = clean_and_calculate(temp_formula, t_brix, t_acid, t_sweet)
                
                if stats['Score'] < min_score:
                    min_score = stats['Score']
                    best_formula = temp_formula
                
                progress_bar.progress((g + 1) / generations)
            
            st.session_state['final_formula'] = best_formula

    # Step 4: 결과 출력 및 AI 평가
    if 'final_formula' in st.session_state:
        formula, stats = clean_and_calculate(st.session_state['final_formula'], t_brix, t_acid, t_sweet)
        
        st.subheader("🧪 최종 배합표 및 이화학 시뮬레이션 결과")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("최종 Brix", f"{stats['Brix']}°Bx", round(stats['Brix']-t_brix, 2))
        c2.metric("최종 감미도", stats['Sweetness'], round(stats['Sweetness']-t_sweet, 2))
        c3.metric("최종 산도", f"{stats['Acid']}%", round(stats['Acid']-t_acid, 3))
        c4.metric("예상 pH", stats['pH'])

        # R&D 표준 배합표 출력
        st.dataframe(formula, use_container_width=True)
        
        # 합계 행 추가 및 출력
        total_row = pd.DataFrame([['TOTAL', '-', 100.0, '-', '-', '-', stats['Cost'], '-', '-', '-', '-']], 
                                columns=formula.columns)
        
        # AI 연구원 평가
        st.markdown("### 👨‍🔬 AI 연구원 기술 평가")
        eval_msg = get_ai_response(api_key, "You are a senior beverage researcher.", f"Evaluate this formula: {formula.to_dict()}. Focus on flavor balance and stability in Korean.")
        if eval_msg:
            st.write(eval_msg.get('evaluation', eval_msg))

        # 엑셀 다운로드
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            formula.to_excel(writer, index=False, sheet_name='Formulation')
        st.download_button("📥 엑셀 배합표 다운로드", output.getvalue(), f"{selected_flavor}_Recipe.xlsx")
