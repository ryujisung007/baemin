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

BEVERAGE_STANDARDS = {
    "Carbonated (탄산음료)": {"brix": 10.0, "acid": 0.22, "sweet": 7.0, "ph_range": (2.5, 4.5), "desc": "청량감 중심"},
    "Juice (과채음료)": {"brix": 12.0, "acid": 0.30, "sweet": 8.0, "ph_range": (2.5, 4.5), "desc": "원료 본연의 맛"},
    "Sports (스포츠음료)": {"brix": 6.0, "acid": 0.12, "sweet": 4.0, "ph_range": (3.0, 4.5), "desc": "전해질 밸런스"},
    "Energy (에너지음료)": {"brix": 12.5, "acid": 0.25, "sweet": 9.0, "ph_range": (2.5, 4.0), "desc": "고카페인 마스킹"},
    "Plant Based (식물성음료)": {"brix": 7.0, "acid": 0.02, "sweet": 3.0, "ph_range": (6.0, 7.5), "desc": "단백질 안정성"}
}

# ==========================================
# 2. 핵심 물리량 계산 엔진 (Data Type Integrity)
# ==========================================

def calculate_formula_stats(df, target_values):
    df_clean = df.copy()
    num_cols = ['Usage_%', 'Brix', 'Acidity', 'Sweetness', 'Cost']
    for col in num_cols:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0).astype(float)

    df_clean['Brix_Contrib'] = df_clean['Usage_%'] * df_clean['Brix'] / 100
    df_clean['Acid_Contrib'] = df_clean['Usage_%'] * df_clean['Acidity'] / 100
    df_clean['Sweet_Contrib'] = df_clean['Usage_%'] * df_clean['Sweetness'] / 100
    df_clean['Cost_Contrib'] = df_clean['Usage_%'] * df_clean['Cost'] / 100

    t_brix = df_clean['Brix_Contrib'].sum()
    t_acid = df_clean['Acid_Contrib'].sum()
    t_sweet = df_clean['Sweet_Contrib'].sum()
    t_cost = df_clean['Cost_Contrib'].sum()
    
    # pH 시뮬레이션
    delta_ph = t_acid / ((df_clean['Usage_%'] * 0.05).sum() + 0.01)
    final_ph = max(2.0, min(8.5, 7.0 - delta_ph))

    score = (abs(t_brix - target_values['brix']) * 50 + 
             abs(t_acid - target_values['acid']) * 1000 + 
             abs(t_sweet - target_values['sweet']) * 40)

    return df_clean, {
        "Brix": round(t_brix, 2), "Acid": round(t_acid, 3), "Sweetness": round(t_sweet, 2),
        "Cost": round(t_cost, 0), "pH": round(final_ph, 2), "Usage_Sum": round(df_clean['Usage_%'].sum(), 4),
        "Score": score
    }

# ==========================================
# 3. OpenAI API 유틸리티 (에러 방지 강화)
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
        return None

# ==========================================
# 4. Streamlit UI
# ==========================================

st.title("🥤 AI 음료 신제품 배합비 개발 플랫폼")

with st.sidebar:
    st.header("🔑 API 설정")
    api_key = st.text_input("OpenAI API Key", type="password")
    selected_type = st.selectbox("음료 유형 선택", list(BEVERAGE_STANDARDS.keys()))
    std = BEVERAGE_STANDARDS[selected_type]
    
    st.subheader("🎯 타겟 물성 조정")
    t_brix = st.slider("Target Brix (°Bx)", 0.0, 20.0, float(std['brix']), 0.1)
    t_sweet = st.slider("Target Sweetness Index", 0.0, 15.0, float(std['sweet']), 0.1)
    t_acid = st.slider("Target Acidity (%)", 0.0, 1.0, float(std['acid']), 0.01)
    targets = {"brix": t_brix, "acid": t_acid, "sweet": t_sweet}

if not api_key:
    st.warning("API 키를 입력하세요.")
else:
    # 표준 가이드라인 출력
    st.subheader(f"📊 {selected_type} 표준 가이드라인")
    g1, g2, g3, g4 = st.columns(4)
    g1.metric("표준 Brix", f"{std['brix']}°Bx")
    g2.metric("표준 감미도", std['sweet'])
    g3.metric("표준 산도", f"{std['acid']}%")
    g4.metric("권장 pH", f"{std['ph_range'][0]} ~ {std['ph_range'][1]}")

    st.markdown("---")
    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.subheader("Step 1: 트렌드 Flavor 생성")
        if st.button("Flavor 생성"):
            res = get_ai_response(api_key, "Create JSON object with key 'flavors' (list).", f"20 trendy flavors for {selected_type}.")
            if res: st.session_state['flavors'] = res['flavors']
        selected_flavor = st.selectbox("최종 선정 맛", st.session_state.get('flavors', ["Flavor를 생성하세요"]))

    with col_r:
        st.subheader("Step 2: AI 원료 마스터 구성")
        if st.button("원료 DB 생성"):
            with st.spinner("원료 데이터 구성 중..."):
                # [연동 강화] 선택된 Flavor 명칭을 프롬프트에 직접 반영
                sys_msg = "You are a beverage scientist. Return JSON key 'ingredients' (list)."
                user_msg = f"Generate 50 ingredients SPECIFICALLY for {selected_flavor} {selected_type}. Include sugars, acids, and {selected_flavor} extracts. Columns: Ingredient, Category, Brix, Acidity, Sweetness, Cost, Purpose."
                res = get_ai_response(api_key, sys_msg, user_msg)
                if res:
                    st.session_state['ing_db'] = pd.DataFrame(res['ingredients'])
                    st.session_state['selected_flavor_name'] = selected_flavor # 맛 정보 저장
                    st.success(f"{selected_flavor} 전용 원료 DB 구축 완료")

    st.markdown("---")

    # Step 3: 최적 배합비 산출 (로직 고도화)
    if 'ing_db' in st.session_state:
        st.subheader(f"Step 3: {st.session_state.get('selected_flavor_name', '')} 최적 배합 시뮬레이션")
        if st.button("배합비 산출 시작"):
            ing_db = st.session_state['ing_db']
            best_formula = None
            min_score = float('inf')
            
            # [타겟 충족 로직] 50회 반복 및 타겟 Scaling 적용
            for _ in range(50):
                temp = ing_db.sample(n=min(len(ing_db), 10)).copy()
                # 1단계: 랜덤 사용량 할당
                raw = np.random.dirichlet(np.ones(len(temp)), size=1)[0] * 15 
                temp['Usage_%'] = raw
                
                # 2단계: 물성 역산 보정 (Target 근사치 강제 조정)
                _, s = calculate_formula_stats(temp, targets)
                ratio = targets['brix'] / (s['Brix'] + 0.01)
                temp['Usage_%'] = temp['Usage_%'] * ratio # Brix 타겟에 맞춰 Scaling
                
                # 3단계: 정제수 밸런싱 (100% 보정)
                current_sum = temp['Usage_%'].sum()
                if current_sum < 95:
                    water_row = pd.DataFrame([{'Ingredient': 'Purified Water', 'Category': 'Base', 'Brix': 0, 'Acidity': 0, 'Sweetness': 0, 'Cost': 30, 'Purpose': 'Solvent', 'Usage_%': 100 - current_sum}])
                    temp = pd.concat([temp, water_row], ignore_index=True)
                    _, s = calculate_formula_stats(temp, targets)
                    if s['Score'] < min_score:
                        min_score = s['Score']; best_formula = temp

            st.session_state['final_formula'] = best_formula

    # Step 4: 결과 출력 및 AI 평가
    if 'final_formula' in st.session_state:
        formula, stats = calculate_formula_stats(st.session_state['final_formula'], targets)
        st.subheader("🧪 시뮬레이션 결과")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("최종 Brix", f"{stats['Brix']}°Bx", f"{round(stats['Brix']-t_brix, 2)}")
        c2.metric("최종 감미도", stats['Sweetness'], f"{round(stats['Sweetness']-t_sweet, 2)}")
        c3.metric("최종 산도", f"{stats['Acid']}%", f"{round(stats['Acid']-t_acid, 3)}")
        c4.metric("예상 pH", stats['pH'])

        st.dataframe(formula, use_container_width=True)
        
        # [AI 평가 강화] JSON 키값을 명확히 지정하여 '생성 불가' 메시지 방지
        st.markdown("### 👨‍🔬 AI Senior Researcher Advice")
        advice_res = get_ai_response(api_key, "You are a beverage R&D scientist. Return JSON object with key 'advice' (string).", f"Evaluate this {st.session_state.get('selected_flavor_name')} recipe. Is it suitable for {selected_type}? Final stats: Brix {stats['Brix']}, Acid {stats['Acid']}. Answer in Korean.")
        if advice_res and 'advice' in advice_res:
            st.success(advice_res['advice'])
        else:
            st.info("평가 데이터를 분석 중이거나 응답 형식이 일치하지 않습니다. 다시 시도해 주세요.")

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            formula.to_excel(writer, index=False, sheet_name='Recipe')
        st.download_button("📥 엑셀 배합표 다운로드", output.getvalue(), "R&D_Recipe.xlsx")
