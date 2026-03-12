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

BEVERAGE_TEMPLATES = {
    "탄산음료": {"brix": (8, 12), "acid": (0.1, 0.3), "ph": (2.5, 4.5)},
    "과채음료": {"brix": (8, 14), "acid": (0.1, 0.35), "ph": (2.5, 4.5)},
    "스포츠음료": {"brix": (4, 7), "acid": (0.05, 0.2), "ph": (3.0, 4.5)},
    "에너지음료": {"brix": (10, 14), "acid": (0.1, 0.3), "ph": (2.5, 4.0)},
    "식물성음료": {"brix": (3, 10), "acid": (0, 0.1), "ph": (6.0, 7.5)}
}

# ==========================================
# 2. 핵심 로직 함수 (에러 수정 포인트: 데이터 타입 강제 변환)
# ==========================================

def calculate_properties(formula_df: pd.DataFrame):
    """
    배합표 데이터를 기반으로 최종 물성 계산
    수정 사항: 계산 전 모든 수치형 컬럼을 float로 강제 변환하여 TypeError 방지
    """
    df = formula_df.copy()
    
    # [수정] 수치 계산이 필요한 컬럼들을 강제로 숫자형으로 변환 (오류 발생 지점 해결)
    numeric_cols = ['Usage_%', 'Brix', 'Acidity', 'Sweetness', 'Cost']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 기본 가산 모델 계산
    total_usage = df['Usage_%'].sum()
    total_brix = (df['Usage_%'] * df['Brix'] / 100).sum()
    total_acid = (df['Usage_%'] * df['Acidity'] / 100).sum()
    total_sweetness = (df['Usage_%'] * df['Sweetness'] / 100).sum()
    total_cost = (df['Usage_%'] * df['Cost'] / 100).sum()
    
    # pH 완충 모델
    base_ph = 7.0
    buffer_capacity = (df['Usage_%'] * 0.05).sum()
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
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"API 호출 중 오류 발생: {e}")
        return None

# ==========================================
# 4. UI 레이아웃
# ==========================================

st.title("🥤 AI Beverage R&D Master Platform")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ System Control")
    api_key = st.text_input("OpenAI API Key", type="password")
    bev_type = st.selectbox("음료 유형 선택", list(BEVERAGE_TEMPLATES.keys()))
    
    st.subheader("🎯 Target Properties")
    t_brix = st.slider("Target Brix", 0.0, 20.0, 11.0)
    t_sweet = st.slider("Target Sweetness", 0.0, 15.0, 7.0)
    t_acid = st.slider("Target Acidity", 0.0, 1.0, 0.22)

if not api_key:
    st.warning("API 키를 입력해주세요.")
else:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Step 1: Trend Flavor Analysis")
        if st.button("Generate Trend Flavors"):
            system_msg = "You are a beverage trend analyst. Return a JSON object with a list 'flavors' containing 20 trendy names."
            user_msg = f"Provide 20 trendy flavor names for {bev_type}."
            res = call_openai(api_key, system_msg, user_msg)
            if res:
                st.session_state['flavors'] = json.loads(res).get('flavors', [])

        selected_flavor = st.selectbox("Select Target Flavor", st.session_state.get('flavors', ["Flavor를 먼저 생성하세요"]))

    with col2:
        st.subheader("Step 2: Ingredient DB Generation")
        if st.button("Create AI Ingredient DB"):
            with st.spinner("원료 데이터 생성 중..."):
                system_msg = "You are a food scientist. Create a JSON list 'ingredients' of 50 ingredients. Each must have: Ingredient, Category, Brix (number), pH (number), Acidity (number), Sweetness (number), Cost (number), Purpose."
                user_msg = f"Generate 50 specialized ingredients for a '{selected_flavor}' flavored {bev_type}."
                res = call_openai(api_key, system_msg, user_msg)
                if res:
                    ing_data = json.loads(res).get('ingredients', [])
                    st.session_state['ing_db'] = pd.DataFrame(ing_data)
                    st.success("원료 DB 생성 완료")

    st.markdown("---")
    
    if 'ing_db' in st.session_state:
        st.subheader("Step 3: Optimization & Final Formulation")
        
        if st.button("Run AI Optimization"):
            ing_db = st.session_state['ing_db']
            
            # [수정] 샘플링 시 데이터 타입 안전성 확보를 위해 .copy() 사용
            formula = ing_db.sample(min(len(ing_db), 7)).copy()
            
            # 임시 사용량 배분 (나중에 유전 알고리즘으로 대체될 부분)
            raw_usages = np.random.dirichlet(np.ones(len(formula)), size=1)[0] * 15
            formula['Usage_%'] = raw_usages
            
            water_row = {
                'Ingredient': 'Purified Water', 'Category': 'Base', 'Brix': 0, 'pH': 7.0, 
                'Acidity': 0, 'Sweetness': 0, 'Cost': 50, 'Purpose': 'Solvent', 
                'Usage_%': 100 - formula['Usage_%'].sum()
            }
            formula = pd.concat([formula, pd.DataFrame([water_row])], ignore_index=True)
            
            # [핵심] 물성 계산 전 최종 데이터 검증
            try:
                stats = calculate_properties(formula)
                
                # 결과 UI 출력
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Final Brix", f"{stats['Brix']}°Bx")
                c2.metric("Final pH", stats['pH'])
                c3.metric("Total Acidity", f"{stats['Acid']}%")
                c4.metric("Sweetness Index", stats['Sweetness'])
                c5.metric("Cost per kg", f"₩{stats['Cost']}")

                st.dataframe(formula, use_container_width=True)
                
                # 다운로드 기능
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    formula.to_excel(writer, index=False, sheet_name='Formulation')
                st.download_button(label="Excel 다운로드", data=output.getvalue(), file_name=f"{selected_flavor}_Recipe.xlsx")
                
            except Exception as e:
                st.error(f"계산 중 오류 발생: {e}. 데이터 형식을 확인하세요.")
