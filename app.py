import streamlit as st
import pandas as pd
import numpy as np
import openai
import json
import io

# ==========================================
# 1. 환경 설정 및 표준 배합 가이드라인
# ==========================================
st.set_page_config(page_title="AI Beverage R&D Platform", layout="wide")

# 음료 유형별 표준 가이드라인 (식품공전 및 R&D 표준 기반)
BEVERAGE_STANDARDS = {
    "Carbonated (탄산음료)": {"brix": 10.0, "acid": 0.22, "sweet": 7.0, "ph_range": (2.5, 4.5), "desc": "청량감 중심, 높은 탄산 압력 대응"},
    "Juice (과채음료)": {"brix": 12.0, "acid": 0.30, "sweet": 8.0, "ph_range": (2.5, 4.5), "desc": "원료 본연의 맛과 점도 유지 중요"},
    "Sports (스포츠음료)": {"brix": 6.0, "acid": 0.12, "sweet": 4.0, "ph_range": (3.0, 4.5), "desc": "전해질 밸런스 및 빠른 흡수 설계"},
    "Energy (에너지음료)": {"brix": 12.5, "acid": 0.25, "sweet": 9.0, "ph_range": (2.5, 4.0), "desc": "고카페인/타우린 마스킹 설계 필요"},
    "Plant Based (식물성음료)": {"brix": 7.0, "acid": 0.02, "sweet": 3.0, "ph_range": (6.0, 7.5), "desc": "단백질 안정성 및 침전 방지 핵심"}
}

# ==========================================
# 2. 핵심 물리량 계산 엔진 (Data Type Integrity 확보)
# ==========================================

def calculate_formula_stats(df, target_values):
    """배합표의 물성 계산 및 목표 대비 오차(Score) 산출"""
    df_clean = df.copy()
    num_cols = ['Usage_%', 'Brix', 'Acidity', 'Sweetness', 'Cost']
    
    # [방어 코딩] 모든 수치형 컬럼을 float로 강제 변환 (TypeError 방지)
    for col in num_cols:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0).astype(float)

    # 개별 물성 기여도 계산
    df_clean['Brix_Contrib'] = df_clean['Usage_%'] * df_clean['Brix'] / 100
    df_clean['Acid_Contrib'] = df_clean['Usage_%'] * df_clean['Acidity'] / 100
    df_clean['Sweet_Contrib'] = df_clean['Usage_%'] * df_clean['Sweetness'] / 100
    df_clean['Cost_Contrib'] = df_clean['Usage_%'] * df_clean['Cost'] / 100

    # 합계 산출
    total_brix = df_clean['Brix_Contrib'].sum()
    total_acid = df_clean['Acid_Contrib'].sum()
    total_sweet = df_clean['Sweet_Contrib'].sum()
    total_cost = df_clean['Cost_Contrib'].sum()
    total_usage = df_clean['Usage_%'].sum()

    # pH 시뮬레이션 (Henderson-Hasselbalch 기반 약식 모델)
    base_ph = 7.0
    buffer_capacity = (df_clean['Usage_%'] * 0.05).sum()
    delta_ph = total_acid / (buffer_capacity + 0.01)
    final_ph = max(2.0, min(8.5, base_ph - delta_ph))

    # 최적화 점수 (Loss Function)
    score = (abs(total_brix - target_values['brix']) * 40 + 
             abs(total_acid - target_values['acid']) * 600 + 
             abs(total_sweet - target_values['sweet']) * 30)

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
# 3. OpenAI API 유틸리티
# ==========================================

def get_ai_response(api_key, system_msg, user_msg):
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"AI API 연동 오류: {e}")
        return None

# ==========================================
# 4. Streamlit UI 렌더링
# ==========================================

st.title("🥤 AI 음료 신제품 배합비 개발 플랫폼")
st.markdown("---")

with st.sidebar:
    st.header("🔑 API 설정")
    api_key = st.text_input("OpenAI API Key", type="password")
    
    st.header("📋 신제품 조건 설정")
    selected_type = st.selectbox("음료 유형 선택", list(BEVERAGE_STANDARDS.keys()))
    std = BEVERAGE_STANDARDS[selected_type]
    
    st.subheader("🎯 타겟 물성 조정 (표준 기반)")
    t_brix = st.slider("Target Brix (°Bx)", 0.0, 20.0, float(std['brix']), 0.1)
    t_sweet = st.slider("Target Sweetness Index", 0.0, 15.0, float(std['sweet']), 0.1)
    t_acid = st.slider("Target Acidity (%)", 0.0, 1.0, float(std['acid']), 0.01)
    
    targets = {"brix": t_brix, "acid": t_acid, "sweet": t_sweet}

if not api_key:
    st.warning("계속하려면 사이드바에 OpenAI API Key를 입력하세요.")
else:
    # [에러 해결 지점] 상단 표준 가이드라인 출력
    st.subheader(f"📊 {selected_type} 표준 가이드라인")
    g1, g2, g3, g4 = st.columns(4)
    g1.metric("표준 Brix", f"{std['brix']}°Bx")
    g2.metric("표준 감미도", std['sweet'])
    g3.metric("표준 산도", f"{std['acid']}%")
    
    # pH 범위(Tuple)를 문자열로 변환하여 에러 방지
    ph_display = f"{std['ph_range'][0]} ~ {std['ph_range'][1]}"
    g4.metric("권장 pH", ph_display)
    st.caption(f"💡 가이드: {std['desc']}")

    st.markdown("---")

    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.subheader("Step 1: 트렌드 Flavor 생성")
        if st.button("신제품 컨셉/맛 20개 생성"):
            res = get_ai_response(api_key, "You are a beverage marketing expert.", f"Generate 20 trendy flavor names for {selected_type} in JSON list 'flavors'.")
            if res: st.session_state['flavors'] = res['flavors']
        
        selected_flavor = st.selectbox("최종 선정 맛", st.session_state.get('flavors', ["Flavor를 생성하세요"]))

    with col_r:
        st.subheader("Step 2: AI 원료 마스터 구성")
        if st.button("AI 원료 50종 DB 생성"):
            with st.spinner("전문가급 원료 데이터를 수집 중..."):
                sys_msg = "You are a beverage R&D scientist. Create a JSON list 'ingredients' of 50 ingredients. Each: Ingredient, Category, Brix, Acidity, Sweetness, Cost, Purpose."
                user_msg = f"Generate 50 specialized ingredients for {selected_flavor} {selected_type}."
                res = get_ai_response(api_key, sys_msg, user_msg)
                if res:
                    st.session_state['ing_db'] = pd.DataFrame(res['ingredients'])
                    st.success("원료 DB 구축 완료")

    st.markdown("---")

    # Step 3: 최적 배합비 산출
    if 'ing_db' in st.session_state:
        st.subheader("Step 3: 배합 최적화 시뮬레이션")
        if st.button("최적 배합비 산출 (AI Simulation)"):
            ing_db = st.session_state['ing_db']
            
            # 유전 알고리즘 모사 및 최적 배합 탐색
            best_formula = None
            min_score = float('inf')
            
            # 빠른 시뮬레이션을 위해 20회 반복 중 최적값 탐색
            for _ in range(20):
                temp = ing_db.sample(n=min(len(ing_db), 8)).copy()
                raw_usages = np.random.dirichlet(np.ones(len(temp)), size=1)[0] * 12
                temp['Usage_%'] = raw_usages
                
                # 정제수 밸런싱
                water_row = pd.DataFrame([{
                    'Ingredient': 'Purified Water', 'Category': 'Base', 'Brix': 0, 'Acidity': 0, 
                    'Sweetness': 0, 'Cost': 30, 'Purpose': 'Solvent', 'Usage_%': 100 - temp['Usage_%'].sum()
                }])
                temp = pd.concat([temp, water_row], ignore_index=True)
                
                _, stats = calculate_formula_stats(temp, targets)
                if stats['Score'] < min_score:
                    min_score = stats['Score']
                    best_formula = temp
            
            st.session_state['final_formula'] = best_formula

    # Step 4: 배합표 출력 및 AI 평가
    if 'final_formula' in st.session_state:
        formula, stats = calculate_formula_stats(st.session_state['final_formula'], targets)
        
        st.subheader("🧪 AI 신제품 표준 배합표")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("최종 Brix", f"{stats['Brix']}°Bx", f"{round(stats['Brix']-t_brix, 2)}")
        c2.metric("최종 감미도", stats['Sweetness'], f"{round(stats['Sweetness']-t_sweet, 2)}")
        c3.metric("최종 산도", f"{stats['Acid']}%", f"{round(stats['Acid']-t_acid, 3)}")
        c4.metric("예상 pH", stats['pH'])

        # 결과 테이블 렌더링
        st.dataframe(formula[['Ingredient', 'Usage_%', 'Brix', 'Acidity', 'Sweetness', 'Cost', 'Purpose']], use_container_width=True)
        
        # 합계 검증
        if abs(stats['Usage_Sum'] - 100) < 0.01:
            st.success("✅ 배합 합계 100.0% 확인됨")
        
        # AI 연구원 조언
        st.markdown("### 👨‍🔬 AI Senior Researcher Advice")
        advice_res = get_ai_response(api_key, "You are a senior beverage researcher.", f"Provide a brief R&D evaluation for this formula: {formula.to_dict()} in Korean JSON format 'evaluation'.")
        if advice_res:
            st.write(advice_res.get('evaluation', '평가를 생성할 수 없습니다.'))

        # 엑셀 다운로드
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            formula.to_excel(writer, index=False, sheet_name='Recipe')
        st.download_button("📥 배합표 엑셀 다운로드", output.getvalue(), f"R&D_Recipe_{selected_flavor}.xlsx")
