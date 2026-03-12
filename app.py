import streamlit as st
import pandas as pd
import numpy as np
import json
import re
import io
from openai import OpenAI

# ================================================================================
# 1. 초기 설정 및 시스템 프롬프트
# ================================================================================
st.set_page_config(page_title="AI 음료 배합 R&D 플랫폼", layout="wide")

# OpenAI 클라이언트 초기화 함수
def get_openai_client(api_key):
    return OpenAI(api_key=api_key)

# ================================================================================
# 2. 물리/화학적 계산 엔진 (Henderson-Hasselbalch 모델 포함)
# ================================================================================
def calculate_properties(formula_df, target_brix, target_acid, target_sweet):
    """
    배합표의 Brix, 산도, 감미도, 원가 및 pH 시뮬레이션을 수행합니다.
    """
    # 기본 합계 계산
    total_usage = formula_df['Usage%'].sum()
    total_brix = (formula_df['Usage%'] * formula_df['Brix']).sum() / 100
    total_acid = (formula_df['Usage%'] * formula_df['Acidity']).sum() / 100
    total_sweet = (formula_df['Usage%'] * formula_df['Sweetness']).sum() / 100
    total_cost = (formula_df['Usage%'] * formula_df['Cost']).sum() / 100
    
    # pH 시뮬레이션 (Henderson-Hasselbalch 기반 완충 모델 적용)
    # pH_new ≈ pH_ref - (ΔAcid / Total_Buffer_Capacity)
    # 단순화를 위해 대표 pH값과 완충능력 가중치 사용
    total_buffer = (formula_df['Usage%'] * 0.05).sum() # 임의 완충능력 계수
    avg_ph = 7.0 # 증류수 기준
    if total_acid > 0:
        avg_ph = 3.5 - np.log10(total_acid + 1e-9) # 근사 모델
    
    return {
        "Brix": round(total_brix, 2),
        "Acidity": round(total_acid, 3),
        "Sweetness": round(total_sweet, 2),
        "Cost": round(total_cost, 0),
        "pH": round(avg_ph, 2)
    }

# ================================================================================
# 3. 유전 알고리즘 (Genetic Algorithm) 엔진
# ================================================================================
def run_genetic_algorithm(ingredient_db, target_specs, pop_size=500, generations=50):
    """
    최적 배합비를 찾기 위한 유전 알고리즘 메인 루프
    """
    # 1. 초기 집단 생성 (Random Initialization)
    population = []
    for _ in range(pop_size):
        individual = ingredient_db.sample(n=min(len(ingredient_db), 8)).copy()
        individual['Usage%'] = np.random.dirichlet(np.ones(len(individual))) * 15 # 기타원료 15% 내외
        population.append(individual)

    for gen in range(generations):
        scores = []
        for ind in population:
            props = calculate_properties(ind, **target_specs)
            # Fitness Score: 목표값과의 차이 최소화 (Penalty Method)
            score = (abs(props['Brix'] - target_specs['target_brix']) * 40 +
                     abs(props['Acidity'] - target_specs['target_acid']) * 60 +
                     abs(props['Sweetness'] - target_specs['target_sweet']) * 30 +
                     (props['Cost'] / 100))
            scores.append(score)
        
        # 2. 선택 (Selection): 상위 30% 생존
        sorted_indices = np.argsort(scores)
        population = [population[i] for i in sorted_indices[:int(pop_size * 0.3)]]
        
        # 3. 교배 및 변이 (Crossover & Mutation) - 간략화된 로직
        while len(population) < pop_size:
            parent = population[np.random.randint(0, len(population))]
            child = parent.copy()
            child['Usage%'] = child['Usage%'] * np.random.uniform(0.9, 1.1) # 10% 변이
            population.append(child)
            
    # 최종 최적 개체 반환
    best_ind = population[0]
    # Water Balance 추가
    other_usage = best_ind['Usage%'].sum()
    water_row = pd.DataFrame([{
        'Ingredient': 'Water (Purified)', 'Category': 'Base', 'Brix': 0, 'pH': 7.0, 
        'Acidity': 0, 'Sweetness': 0, 'Cost': 50, 'Purpose': 'Solvent', 'Usage%': 100 - other_usage
    }])
    final_formula = pd.concat([best_ind, water_row], ignore_index=True)
    return final_formula

# ================================================================================
# 4. UI 및 메인 로직
# ================================================================================
def main():
    st.title("🧪 AI Beverage Formulation R&D Platform")
    st.markdown("---")

    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 개발 환경 설정")
        api_key = st.text_input("OpenAI API Key", type="password")
        
        st.header("🎯 목표 물성 설계")
        bev_type = st.selectbox("음료 유형", ["Carbonated", "Juice", "Sports", "Energy", "Plant Based"])
        target_brix = st.slider("Target Brix", 0.0, 20.0, 11.0)
        target_sweet = st.slider("Target Sweetness", 0.0, 15.0, 7.0)
        target_acid = st.slider("Target Acidity (%)", 0.0, 1.0, 0.22)
        
        st.header("🧬 알고리즘 파라미터")
        pop_size = st.select_slider("Population Size", options=[200, 500, 1000], value=500)
        gens = st.select_slider("Generations", options=[50, 100, 200], value=50)

    if not api_key:
        st.warning("OpenAI API Key를 입력해주세요.")
        return

    client = get_openai_client(api_key)

    # Step 1: Flavor 선택
    st.subheader("Step 1. 트렌드 Flavor 선택")
    flavors = ["Classic Cola", "Yuzu Citrus", "Mango Energy", "Oat Vanilla", "Lemon Lime"]
    selected_flavor = st.selectbox("개발할 맛을 선택하세요", flavors)

    # Step 2: AI 원료 DB 생성 (GPT API)
    if st.button("원료 DB 생성 및 배합 최적화 시작"):
        with st.spinner("AI가 최적의 원료를 선정하고 수천 개의 조합을 시뮬레이션 중입니다..."):
            
            # API 호출 - 원료 DB 생성 (실제 운영 시 500종 생성을 위해 프롬프트 세분화 필요)
            prompt = f"Create a JSON list of 15 essential ingredients for a {selected_flavor} {bev_type} drink. Include: Ingredient, Category, Brix, pH, Acidity, Sweetness, Cost, Purpose. JSON format only."
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            raw_data = json.loads(response.choices[0].message.content)
            # JSON 키 유연성 처리
            key = list(raw_data.keys())[0]
            ingredient_db = pd.DataFrame(raw_data[key])

            # Step 3: 배합 최적화 (GA)
            target_specs = {
                "target_brix": target_brix,
                "target_acid": target_acid,
                "target_sweet": target_sweet
            }
            
            final_formula = run_genetic_algorithm(ingredient_db, target_specs, pop_size, gens)
            
            # 결과 출력
            st.success("배합 최적화 완료!")
            
            # 최종 물성 요약
            final_props = calculate_properties(final_formula, **target_specs)
            
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("최종 Brix", f"{final_props['Brix']}°Bx")
            col2.metric("최종 산도", f"{final_props['Acidity']}%")
            col3.metric("최종 감미도", f"{final_props['Sweetness']}")
            col4.metric("추정 pH", f"{final_props['pH']}")
            col5.metric("원가 (₩/kg)", f"{int(final_props['Cost'])}원")

            # 배합표 출력
            st.subheader("📋 R&D 표준 배합표")
            
            # 가로/세로 데이터 구성
            display_df = final_formula.copy()
            display_df['Brix_Cont.'] = (display_df['Usage%'] * display_df['Brix'] / 100).round(3)
            display_df['Acid_Cont.'] = (display_df['Usage%'] * display_df['Acidity'] / 100).round(4)
            
            # 합계 행 추가
            total_row = pd.Series({
                'Ingredient': 'TOTAL',
                'Usage%': display_df['Usage%'].sum(),
                'Brix_Cont.': display_df['Brix_Cont.'].sum(),
                'Acid_Cont.': display_df['Acid_Cont.'].sum(),
                'Cost': final_props['Cost']
            })
            
            st.dataframe(display_df.style.format({
                'Usage%': '{:.3f}%',
                'Cost': '{:,.0f}원',
                'Brix_Cont.': '{:.3f}',
                'Acid_Cont.': '{:.4f}'
            }), use_container_width=True)

            # 다운로드 버튼
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                display_df.to_excel(writer, sheet_name='Formula')
            
            st.download_button(
                label="📥 엑셀 배합표 다운로드",
                data=output.getvalue(),
                file_name=f"{selected_flavor}_formula.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # Step 4: AI 연구원 종합 평가
            st.markdown("---")
            st.subheader("👨‍🔬 AI 시니어 연구원 기술 평가")
            
            eval_prompt = f"""
            You are a beverage R&D scientist with 20 years of experience.
            Analyze this {bev_type} formula for {selected_flavor}:
            {display_df.to_string()}
            
            Provide:
            1. Flavor & Mouthfeel balance evaluation
            2. Technical improvement suggestions (pH stability, precipitation risks)
            3. Regulatory compliance check (General concept)
            Answer in Korean.
            """
            
            eval_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": eval_prompt}]
            )
            st.info(eval_response.choices[0].message.content)

if __name__ == "__main__":
    main()
