import streamlit as st
import pandas as pd
import numpy as np
import openai
import json
import io

# ==========================================
# 1. 초기 설정 및 표준 가이드라인 데이터
# ==========================================
st.set_page_config(page_title="Beverage AI R&D Platform", layout="wide")

# 식품공전 및 R&D 표준 가이드라인 (A단계 연동)
BEVERAGE_STANDARDS = {
    "탄산음료": {"brix": 10.0, "acid": 0.22, "sweet": 7.0, "ph_range": "2.5~4.5", "desc": "청량감 중심, 높은 탄산 압력 대응"},
    "과채음료": {"brix": 12.0, "acid": 0.30, "sweet": 8.0, "ph_range": "2.5~4.5", "desc": "원료 본연의 맛과 점도 유지 중요"},
    "스포츠음료": {"brix": 6.0, "acid": 0.12, "sweet": 4.0, "ph_range": "3.0~4.5", "desc": "전해질 밸런스 및 빠른 흡수 설계"},
    "에너지음료": {"brix": 12.5, "acid": 0.25, "sweet": 9.0, "ph_range": "2.5~4.0", "desc": "고카페인/타우린 마스킹 설계 필요"},
    "식물성음료": {"brix": 7.0, "acid": 0.02, "sweet": 3.0, "ph_range": "6.0~7.5", "desc": "단백질 안정성 및 침전 방지 핵심"}
}

# ==========================================
# 2. 데이터 처리 및 계산 엔진
# ==========================================

def calculate_formula_stats(df: pd.DataFrame):
    """배합표의 물리적 특성 계산 (Type Safety 확보)"""
    temp_df = df.copy()
    num_cols = ['Usage_%', 'Brix', 'Acidity', 'Sweetness', 'Cost']
    for col in num_cols:
        temp_df[col] = pd.to_numeric(temp_df[col], errors='coerce').fillna(0)

    total_usage = temp_df['Usage_%'].sum()
    res = {
        "Brix": (temp_df['Usage_%'] * temp_df['Brix'] / 100).sum(),
        "Acid": (temp_df['Usage_%'] * temp_df['Acidity'] / 100).sum(),
        "Sweetness": (temp_df['Usage_%'] * temp_df['Sweetness'] / 100).sum(),
        "Cost": (temp_df['Usage_%'] * temp_df['Cost'] / 100).sum(),
        "Usage_Sum": total_usage
    }
    return res

# ==========================================
# 3. UI 구성 및 메인 로직
# ==========================================

st.title("🧪 AI 신제품 배합비 개발 플랫폼")
st.info("음료 유형을 선택하면 표준 가이드라인이 로드되며, 사용자의 조정 값이 AI 최적화 타겟으로 연동됩니다.")

# --- 사이드바: 입력 및 조정 ---
with st.sidebar:
    st.header("1. 기본 설정")
    api_key = st.text_input("OpenAI API Key", type="password")
    
    # [연동 포인트] 음료 유형 선택
    selected_type = st.selectbox("음료 유형 선택", list(BEVERAGE_STANDARDS.keys()))
    std = BEVERAGE_STANDARDS[selected_type]
    
    st.markdown("---")
    st.header("2. 목표 물성 조정 (AI 타겟)")
    # [연동 포인트] 표준값을 기본값으로 설정하는 슬라이더
    target_brix = st.slider("목표 Brix (°Bx)", 0.0, 20.0, float(std['brix']), step=0.1)
    target_sweet = st.slider("목표 감미도 (Sweetness Index)", 0.0, 15.0, float(std['sweet']), step=0.1)
    target_acid = st.slider("목표 산도 (Acidity %)", 0.0, 1.0, float(std['acid']), step=0.01)

# --- 메인 화면: 가이드라인 및 결과 ---
if not api_key:
    st.warning("계속하려면 사이드바에 OpenAI API Key를 입력하세요.")
else:
    # 상단: 선택된 유형의 표준 가이드라인 출력
    st.subheader(f"📊 {selected_type} 표준 가이드라인")
    g1, g2, g3, g4 = st.columns(4)
    g1.metric("표준 Brix", f"{std['brix']}°Bx")
    g2.metric("표준 감미도", std['sweet'])
    g3.metric("표준 산도", f"{std['acid']}%")
    g4.metric("권장 pH 범위", std['ph_range'])
    st.caption(f"💡 설계 팁: {std['desc']}")

    st.markdown("---")

    # Step 1: AI 원료 DB 생성 (이미 생성된 경우 재사용 가능하도록 세션 관리)
    if st.button(f"'{selected_type}' 맞춤형 AI 원료 DB 및 배합 생성"):
        with st.spinner("AI 연구원이 원료를 선별하고 최적 배합을 구성 중입니다..."):
            
            # AI 프롬프트 (JSON 모드 사용)
            system_prompt = f"""You are a senior beverage scientist. 
            Create a formulation for {selected_type}. 
            The goal is Brix:{target_brix}, Sweetness:{target_sweet}, Acidity:{target_acid}.
            Return a JSON object with 'ingredients' list. 
            Each ingredient must have: Ingredient, Category, Brix, Acidity, Sweetness, Cost, Usage_%, Purpose."""
            
            user_prompt = f"Create a real-world formula for {selected_type}. The usage sum must be exactly 100% including Purified Water."
            
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                response_format={"type": "json_object"}
            )
            
            res_data = json.loads(response.choices[0].message.content)
            formula_df = pd.DataFrame(res_data['ingredients'])
            
            # 데이터 타입 강제 변환 (오류 방지)
            for col in ['Usage_%', 'Brix', 'Acidity', 'Sweetness', 'Cost']:
                formula_df[col] = pd.to_numeric(formula_df[col], errors='coerce').fillna(0)
            
            st.session_state['current_formula'] = formula_df

    # Step 2: 결과 분석 및 출력
    if 'current_formula' in st.session_state:
        formula = st.session_state['current_formula']
        stats = calculate_formula_stats(formula)
        
        st.subheader("🧪 AI 자동 생성 배합 결과")
        
        # 목표값 대비 달성도 시각화
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("최종 Brix", f"{round(stats['Brix'], 2)}°Bx", f"{round(stats['Brix'] - target_brix, 2)}")
        c2.metric("최종 감미도", round(stats['Sweetness'], 2), f"{round(stats['Sweetness'] - target_sweet, 2)}")
        c3.metric("최종 산도", f"{round(stats['Acid'], 3)}%", f"{round(stats['Acid'] - target_acid, 3)}")
        c4.metric("원가 (1kg)", f"₩{int(stats['Cost'])}")

        # 배합표 (R&D 표준 양식)
        st.dataframe(formula.style.highlight_max(axis=0, subset=['Usage_%']), use_container_width=True)
        
        # 합계 검증
        if abs(stats['Usage_Sum'] - 100) > 0.01:
            st.warning(f"⚠️ 배합 합계가 {stats['Usage_Sum']}%입니다. 100%가 되도록 조정이 필요할 수 있습니다.")
        else:
            st.success("✅ 배합 합계 100.0% 확인됨")

        # 엑셀 다운로드
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            formula.to_excel(writer, index=False, sheet_name='Formula')
        st.download_button(label="📄 R&D 배합표 엑셀 다운로드", data=output.getvalue(), file_name=f"{selected_type}_AI_Recipe.xlsx")
