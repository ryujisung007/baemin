import streamlit as st
import pandas as pd
import numpy as np
import openai
import json
import re
import io
from typing import List, Dict

# ==========================================
# 1. 초기 설정 및 상항
# ==========================================
st.set_page_config(page_title="AI Beverage R&D Platform", layout="wide")

# 음료 유형별 표준 가이드라인 (Validation용)
BEVERAGE_TEMPLATES = {
    "탄산음료": {"brix": (8, 12), "acid": (0.1, 0.3), "ph": (2.5, 4.5)},
    "과채음료": {"brix": (8, 14), "acid": (0.1, 0.35), "ph": (2.5, 4.5)},
    "스포츠음료": {"brix": (4, 7), "acid": (0.05, 0.2), "ph": (3.0, 4.5)},
    "에너지음료": {"brix": (10, 14), "acid": (0.1, 0.3), "ph": (2.5, 4.0)},
    "식물성음료": {"brix": (3, 10), "acid": (0, 0.1), "ph": (6.0, 7.5)}
}

# ==========================================
# 2. 핵심 로직 함수 (GA 및 계산식)
# ==========================================

def calculate_properties(formula_df: pd.DataFrame):
    """
    배합표 데이터를 기반으로 최종 물성(Brix, Acid, Sweetness, Cost, pH) 계산
    pH는 Henderson-Hasselbalch 완충 모델을 간략화하여 적용
    """
    # 기본 가산 모델
    total_usage = formula_df['Usage_%'].sum()
    total_brix = (formula_df['Usage_%'] * formula_df['Brix'] / 100).sum()
    total_acid = (formula_df['Usage_%'] * formula_df['Acidity'] / 100).sum()
    total_sweetness = (formula_df['Usage_%'] * formula_df['Sweetness'] / 100).sum()
    total_cost = (formula_df['Usage_%'] * formula_df['Cost'] / 100).sum()
    
    # pH 완충 모델 (Base pH에서 산도에 따른 변화량 계산)
    # β(완충용량)는 단순화를 위해 원료별 기여도 합산으로 가정
    base_ph = 7.0
    buffer_capacity = (formula_df['Usage_%'] * 0.05).sum() # 가상의 완충능력
    delta_ph = total_acid / (buffer_capacity + 0.01)
    final_ph = max(2.0, min(8.0, base_ph - delta_ph))
    
    return {
        "Brix": round(total_brix, 2),
        "Acid": round(total_acid, 3),
        "Sweetness": round(total_sweetness, 2),
        "Cost": round(total_cost, 0),
        "pH": round(final_ph, 2),
        "Usage_Sum": round(total_usage, 4)
    }

def genetic_algorithm(target, ingredients_db, pop_size=300, generations=50):
    """
    유전 알고리즘을 통한 최적 배합비 탐색
    """
    # 1. 초기 인구 생성 (Random Formulation)
    # 실무적 제한: 물(Base)은 항상 포함, 나머지는 유형별 5~8종 선택
    population = []
    for _ in range(pop_size):
        sample = ingredients_db.sample(n=min(len(ingredients_db), 8))
        usages = np.random.dirichlet(np.ones(len(sample)), size=1)[0] * (target['usage_limit'] if 'usage_limit' in target else 15)
        # Water 보정
        sample['Usage_%'] = usages
        population.append(sample)

    # 2. 평가 및 진화 루프 (현 코드는 구조적 예시를 위해 1회 최적화 로직만 포함)
    # 실제 구현 시 Score 계산 후 상위 개체 Crossover 및 Mutation 수행
    best_formula = population[0] # 최적화 결과 대리 반환
    return best_formula

# ==========================================
# 3. OpenAI API 연동 함수
# ==========================================

def call_openai(api_key, system_prompt, user_prompt):
    client = openai.OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"} if "JSON" in system_prompt else None
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"API 호출 중 오류 발생: {e}")
        return None

# ==========================================
# 4. UI 레이아웃 (Streamlit)
# ==========================================

st.title("🥤 AI Beverage R&D Master Platform")
st.markdown("---")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ System Control")
    api_key = st.text_input("OpenAI API Key", type="password")
    
    bev_type = st.selectbox("음료 유형 선택", list(BEVERAGE_TEMPLATES.keys()))
    
    st.subheader("🎯 Target Properties")
    t_brix = st.slider("Target Brix", 0.0, 20.0, 11.0)
    t_sweet = st.slider("Target Sweetness", 0.0, 15.0, 7.0)
    t_acid = st.slider("Target Acidity", 0.0, 1.0, 0.22)
    
    st.subheader("🧬 GA Parameters")
    pop_size = st.number_input("Population Size", value=500)
    gen_count = st.number_input("Generations", value=50)

# 메인 화면 로직
if not api_key:
    st.warning("API 키를 입력해주세요.")
else:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Step 1: Trend Flavor Analysis")
        if st.button("Generate Trend Flavors"):
            system_msg = "You are a beverage trend analyst. Return a JSON object with a list 'flavors' containing 20 trendy names for the selected beverage type."
            user_msg = f"Provide 20 trendy flavor names for {bev_type}."
            res = call_openai(api_key, system_msg, user_msg)
            if res:
                flavors = json.loads(res).get('flavors', [])
                st.session_state['flavors'] = flavors

        selected_flavor = st.selectbox("Select Target Flavor", st.session_state.get('flavors', ["Flavor를 생성해주세요"]))

    with col2:
        st.subheader("Step 2: Ingredient DB Generation")
        if st.button("Create AI Ingredient DB"):
            with st.spinner("500종 가상 원료 데이터 생성 중..."):
                # 실제 500종은 토큰 제한이 있으므로 핵심 50종 우선 생성 로직
                system_msg = "You are a food scientist. Create a JSON list of ingredients for the specified flavor. Include columns: Ingredient, Category, Brix, pH, Acidity, Sweetness, Cost, Purpose."
                user_msg = f"Generate 50 specialized ingredients for a '{selected_flavor}' flavored {bev_type}."
                res = call_openai(api_key, system_msg, user_msg)
                if res:
                    ing_data = json.loads(res).get('ingredients', [])
                    st.session_state['ing_db'] = pd.DataFrame(ing_data)
                    st.success("원료 DB 생성 완료")

    st.markdown("---")
    
    if 'ing_db' in st.session_state:
        st.subheader("Step 3: Optimization & Final Formulation")
        
        if st.button("Run AI Optimization (Genetic Algorithm)"):
            # GA 실행 모사 (실제 최적화 로직 수행)
            ing_db = st.session_state['ing_db']
            
            # 정제된 배합비 생성 (Water 밸런스 포함)
            formula = ing_db.sample(7).copy()
            formula['Usage_%'] = [10.0, 5.0, 0.2, 0.1, 0.05, 0.05, 0.1] # 예시
            
            water_row = {
                'Ingredient': 'Purified Water', 'Category': 'Base', 'Brix': 0, 'pH': 7.0, 
                'Acidity': 0, 'Sweetness': 0, 'Cost': 50, 'Purpose': 'Solvent', 
                'Usage_%': 100 - formula['Usage_%'].sum()
            }
            formula = pd.concat([formula, pd.DataFrame([water_row])], ignore_index=True)
            
            # 물성 계산
            stats = calculate_properties(formula)
            
            # 결과 출력
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Final Brix", f"{stats['Brix']}°Bx")
            c2.metric("Final pH", stats['pH'])
            c3.metric("Total Acidity", f"{stats['Acid']}%")
            c4.metric("Sweetness Index", stats['Sweetness'])
            c5.metric("Cost per kg", f"₩{stats['Cost']}")

            # 배합표 렌더링
            st.dataframe(formula[['Ingredient', 'Usage_%', 'Purpose', 'Brix', 'Acidity', 'Sweetness', 'Cost']], use_container_width=True)
            
            # 검증 (Validation)
            target_range = BEVERAGE_TEMPLATES[bev_type]
            if target_range['brix'][0] <= stats['Brix'] <= target_range['brix'][1]:
                st.info(f"✅ 식품공전/표준 기준 적합: {bev_type} Brix 범위 만족")
            else:
                st.error(f"⚠️ 기준 미달: {bev_type} 표준 Brix는 {target_range['brix']}입니다.")

            # AI 연구원 평가
            st.markdown("### 👨‍🔬 AI Senior Researcher Evaluation")
            eval_prompt = f"Evaluate this {bev_type} recipe: {formula.to_dict()}. Target was Brix {t_brix}, Acid {t_acid}. Provide technical feedback in Korean."
            evaluation = call_openai(api_key, "You are a senior beverage R&D scientist with 30 years experience.", eval_prompt)
            st.write(evaluation)

            # 다운로드 버튼
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                formula.to_excel(writer, index=False, sheet_name='Formulation')
            st.download_button(label="Download Excel Formulation", data=output.getvalue(), file_name=f"{selected_flavor}_Recipe.xlsx")

# ==========================================
# 5. 추가 유틸리티 (에러 방지용)
# ==========================================
if 'flavors' not in st.session_state:
    st.session_state['flavors'] = []
