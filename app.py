import io
import os
import math
import random
import base64
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

import pandas as pd
import streamlit as st

# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="오픈AI&식품정보원 음료개발 플랫폼",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULT_EXCEL_PATH = "beverage_AI_DB_v1.xlsx"

# =========================================================
# 디자인
# =========================================================
st.markdown(
    """
    <style>
    :root {
        --bg:#07111f;
        --panel:#0d1b2f;
        --panel2:#11243d;
        --line:#2b537c;
        --cyan:#66d9ff;
        --cyan2:#97f0ff;
        --text:#eef7ff;
        --muted:#9fb8d1;
        --ok:#67e8a5;
        --warn:#ffd166;
        --bad:#ff7b7b;
    }

    .stApp {
        background:
            radial-gradient(circle at 15% 15%, rgba(87,195,255,0.10), transparent 25%),
            radial-gradient(circle at 85% 10%, rgba(102,255,214,0.08), transparent 20%),
            linear-gradient(180deg, #06101d 0%, #0b1524 100%);
        color: var(--text);
    }

    .hero-wrap {
        background: linear-gradient(135deg, rgba(14,29,50,0.95), rgba(10,19,34,0.92));
        border: 1px solid rgba(102,217,255,0.18);
        border-radius: 22px;
        padding: 22px 24px 18px 24px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.28);
        margin-bottom: 14px;
    }

    .hero-title {
        font-size: 2rem;
        font-weight: 900;
        color: #f6fbff;
        letter-spacing: -0.02em;
        margin-bottom: 6px;
    }

    .hero-sub {
        font-size: 0.98rem;
        color: var(--muted);
        margin-bottom: 8px;
    }

    .hero-badge {
        display: inline-block;
        margin-right: 8px;
        margin-bottom: 8px;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(89,207,255,0.10);
        border: 1px solid rgba(89,207,255,0.20);
        color: #dbf8ff;
        font-size: 0.85rem;
    }

    .panel {
        background: linear-gradient(180deg, rgba(13,27,47,0.95), rgba(9,19,34,0.98));
        border: 1px solid rgba(102,217,255,0.16);
        border-radius: 18px;
        padding: 16px 16px 12px 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.20);
        margin-bottom: 14px;
    }

    .panel-title {
        font-size: 1.08rem;
        font-weight: 800;
        color: #e3f7ff;
        margin-bottom: 10px;
    }

    .cockpit {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 10px;
        margin-top: 8px;
        margin-bottom: 2px;
    }

    .cockpit-box {
        background: linear-gradient(180deg, rgba(17,36,61,0.92), rgba(11,23,39,0.96));
        border: 1px solid rgba(102,217,255,0.14);
        border-radius: 14px;
        padding: 10px 12px;
        min-height: 78px;
    }

    .cockpit-label {
        color: var(--muted);
        font-size: 0.78rem;
        margin-bottom: 4px;
    }

    .cockpit-value {
        color: var(--cyan2);
        font-weight: 800;
        font-size: 1.08rem;
    }

    .reason-box {
        background: rgba(10,18,31,0.92);
        border-left: 4px solid #67dfff;
        border-radius: 10px;
        padding: 10px 12px;
        margin-bottom: 8px;
    }

    .mini-pill {
        display:inline-block;
        padding: 4px 8px;
        border-radius:999px;
        background: rgba(102,217,255,0.12);
        color:#def8ff;
        font-size:0.78rem;
        margin-right:6px;
        margin-bottom:6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-wrap">
      <div class="hero-title">🤖 오픈AI&식품정보원 음료개발 플랫폼</div>
      <div class="hero-sub">
        식품연구소 자동화 로봇 조종실 컨셉 · 원재료 DB 생성 · 자동 배합 · 평가보고서 · 제품 이미지 생성
      </div>
      <div>
        <span class="hero-badge">Cockpit Control UI</span>
        <span class="hero-badge">Ingredient Intelligence</span>
        <span class="hero-badge">Formula Optimization</span>
        <span class="hero-badge">R&D + Marketing Review</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 상수
# =========================================================
UI_BEVERAGE_TYPES = [
    "탄산음료",
    "과채음료",
    "스포츠음료",
    "에너지음료",
    "식물성음료",
    "기능성음료",
]

TREND_FLAVORS = {
    "탄산음료": [
        "Classic Cola", "Lemon Lime", "Grapefruit Citrus", "Blood Orange", "Yuzu Citrus",
        "Ginger Ale", "Pineapple Soda", "Mango Sparkling", "Peach Sparkling", "Apple Soda",
        "Berry Mix", "Strawberry Lime", "Watermelon Soda", "Lychee Sparkling",
        "Passionfruit Soda", "Guava Sparkling", "Lemon Mint Soda", "Hibiscus Berry",
        "Cucumber Lime", "Elderflower Citrus",
    ],
    "과채음료": [
        "Mango Orange", "Peach Mango", "Apple Mango", "Apple Peach", "Grape Berry",
        "Pineapple Coconut", "Strawberry Banana", "Mango Passionfruit", "Orange Carrot",
        "Apple Kiwi", "Peach Guava", "Berry Pomegranate", "Apple Ginger", "Lemon Honey",
        "Mango Aloe", "Peach Aloe", "Apple Hibiscus", "Pineapple Mint",
        "Strawberry Lychee", "Mango Dragonfruit",
    ],
    "스포츠음료": [
        "Lemon Lime Electrolyte", "Orange Electrolyte", "Citrus Mix",
        "Grapefruit Electrolyte", "Lemon Honey", "Mango Electrolyte",
        "Peach Electrolyte", "Berry Electrolyte", "Tropical Electrolyte",
        "Watermelon Electrolyte", "Coconut Electrolyte", "Pineapple Electrolyte",
        "Apple Electrolyte", "Lychee Electrolyte", "Passionfruit Electrolyte",
        "Guava Electrolyte", "Lemon Ginger", "Berry Citrus", "Cucumber Lime",
        "Aloe Citrus",
    ],
    "에너지음료": [
        "Classic Energy Citrus", "Tropical Energy", "Mango Energy", "Peach Energy",
        "Berry Energy", "Watermelon Energy", "Apple Energy", "Pineapple Energy",
        "Dragonfruit Energy", "Guava Energy", "Lychee Energy", "Passionfruit Energy",
        "Lemon Energy", "Lime Energy", "Grapefruit Energy", "Yuzu Energy",
        "Mango Peach Energy", "Berry Blast Energy", "Citrus Punch Energy",
        "Tropical Punch Energy",
    ],
    "식물성음료": [
        "Almond Vanilla", "Almond Chocolate", "Oat Vanilla", "Oat Chocolate",
        "Coconut Vanilla", "Coconut Chocolate", "Soy Vanilla", "Soy Chocolate",
        "Almond Matcha", "Oat Matcha", "Coconut Matcha", "Almond Coffee", "Oat Coffee",
        "Coconut Coffee", "Almond Banana", "Oat Banana", "Almond Strawberry",
        "Oat Strawberry", "Coconut Mango", "Oat Mango",
    ],
    "기능성음료": [
        "Lemon Vitamin", "Orange Vitamin", "Berry Vitamin", "Mango Vitamin",
        "Pineapple Vitamin", "Apple Fiber", "Berry Fiber", "Lemon Collagen",
        "Peach Collagen", "Mango Collagen", "Apple Probiotic", "Berry Probiotic",
        "Lemon Ginger", "Apple Ginger", "Honey Lemon", "Yuzu Honey", "Aloe Mango",
        "Aloe Peach", "Hibiscus Berry", "Pomegranate Antioxidant",
    ],
}

TYPE_TEMPLATES = {
    "탄산음료": {
        "Water": (85.0, 90.0),
        "Sugar": (8.0, 12.0),
        "Acid": (0.10, 0.30),
        "Flavor": (0.05, 0.20),
        "Stabilizer": (0.00, 0.03),
        "Color": (0.001, 0.01),
        "Sweetener": (0.00, 0.02),
        "Functional": (0.00, 0.02),
    },
    "과채음료": {
        "Water": (60.0, 80.0),
        "Concentrate": (10.0, 30.0),
        "Sugar": (5.0, 10.0),
        "Acid": (0.10, 0.30),
        "Flavor": (0.05, 0.15),
        "Stabilizer": (0.05, 0.20),
        "Color": (0.00, 0.01),
        "Functional": (0.00, 1.00),
    },
    "스포츠음료": {
        "Water": (90.0, 94.0),
        "Sugar": (4.0, 6.0),
        "Electrolyte": (0.10, 0.30),
        "Acid": (0.05, 0.15),
        "Flavor": (0.05, 0.10),
        "Stabilizer": (0.00, 0.03),
        "Sweetener": (0.00, 0.02),
        "Functional": (0.00, 0.20),
    },
    "에너지음료": {
        "Water": (85.0, 90.0),
        "Sugar": (10.0, 12.0),
        "Acid": (0.10, 0.25),
        "Flavor": (0.05, 0.15),
        "Functional": (0.30, 0.60),
        "Sweetener": (0.00, 0.03),
        "Color": (0.00, 0.01),
        "Stabilizer": (0.00, 0.03),
    },
    "식물성음료": {
        "Water": (70.0, 88.0),
        "Concentrate": (5.0, 18.0),
        "Sugar": (0.0, 6.0),
        "Flavor": (0.03, 0.20),
        "Stabilizer": (0.05, 0.30),
        "Functional": (0.00, 1.00),
        "Sweetener": (0.00, 0.03),
    },
    "기능성음료": {
        "Water": (80.0, 92.0),
        "Sugar": (3.0, 8.0),
        "Acid": (0.08, 0.25),
        "Flavor": (0.05, 0.20),
        "Functional": (0.20, 2.00),
        "Sweetener": (0.00, 0.03),
        "Color": (0.00, 0.01),
        "Stabilizer": (0.00, 0.05),
    },
}

VALIDATION_RANGES = {
    "탄산음료": {"Brix": (8.0, 12.0), "pH": (2.5, 4.5), "Acid": (0.10, 0.30)},
    "과채음료": {"Brix": (8.0, 14.0), "pH": (2.5, 4.5), "Acid": (0.10, 0.35)},
    "스포츠음료": {"Brix": (4.0, 7.0), "pH": (3.0, 4.5), "Acid": (0.05, 0.20)},
    "에너지음료": {"Brix": (10.0, 14.0), "pH": (2.5, 4.0), "Acid": (0.10, 0.30)},
    "식물성음료": {"Brix": (3.0, 10.0), "pH": (6.0, 7.5), "Acid": (0.00, 0.10)},
    "기능성음료": {"Brix": (4.0, 12.0), "pH": (2.8, 4.5), "Acid": (0.05, 0.30)},
}

INTENSITY_LABELS = {
    1: "매우 약함",
    2: "약함",
    3: "중간",
    4: "강함",
    5: "매우 강함",
}

# =========================================================
# 데이터 클래스
# =========================================================
@dataclass
class FormulaSummary:
    total_brix: float
    total_acid: float
    total_sweetness: float
    total_cost: float
    total_ph: float
    score: float


# =========================================================
# 공통 유틸
# =========================================================
def safe_float(value, default=0.0) -> float:
    try:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return default
        return float(value)
    except Exception:
        return default


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    rename_map = {
        "Ingredient": "Ingredient_Name",
        "Ingredient Name": "Ingredient_Name",
        "Ingredient_Name": "Ingredient_Name",
        "원료명": "Ingredient_Name",
        "Category": "Category",
        "분류": "Category",
        "Sub_Category": "Sub_Category",
        "Flavor": "Flavor",
        "Flavor_Name": "Flavor",
        "Brix(°)": "Brix",
        "산도(%)": "Acidity",
        "Acidity": "Acidity",
        "산도": "Acidity",
        "감미도": "Sweetness",
        "Sweetness_Index": "Sweetness",
        "예상단가(원/kg)": "Cost",
        "Cost_per_kg": "Cost",
        "단가": "Cost",
        "Brix기여도(1%)": "Brix_Contribution",
        "산도기여도(1%)": "Acid_Contribution",
        "pH영향도(1%)": "pH_Effect",
        "Buffer_Capacity(β)": "Buffer_Capacity",
        "β": "Buffer_Capacity",
        "Ingredient_ID": "Ingredient_ID",
        "Flavor_ID": "Flavor_ID",
        "Ingredient_Role": "Ingredient_Role",
        "Role": "Ingredient_Role",
        "Function": "Function",
        "Origin": "Origin",
        "Supplier": "Supplier",
        "Solubility": "Solubility",
        "Color": "Color",
    }
    return df.rename(columns=rename_map)


def enforce_numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    df = df.copy()
    for col in cols:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


def robust_json_extract(text: str) -> Optional[dict]:
    if not text:
        return None
    try:
        import json
        return json.loads(text)
    except Exception:
        return None


def get_openai_client(api_key: str):
    if not api_key:
        return None, "API key 미입력"
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key), None
    except Exception as e:
        return None, f"OpenAI 클라이언트 생성 실패: {e}"


def role_to_categories(role: str) -> List[str]:
    role_map = {
        "Water": ["Water"],
        "Sugar": ["Sugar"],
        "Sweetener": ["Sweetener"],
        "Acid": ["Acid"],
        "Flavor": ["Concentrate", "Extract"],
        "Concentrate": ["Concentrate"],
        "Extract": ["Extract"],
        "Stabilizer": ["Stabilizer"],
        "Color": ["Color"],
        "Vitamin": ["Vitamin"],
        "Functional": ["Functional", "Vitamin"],
        "Electrolyte": ["Electrolyte"],
    }
    return role_map.get(role, [role])


def map_intensity_to_value(level: int, low: float, high: float) -> float:
    ratio = {1: 0.10, 2: 0.30, 3: 0.50, 4: 0.75, 5: 0.95}.get(level, 0.50)
    return round(low + (high - low) * ratio, 4)


# =========================================================
# 핵심 스키마 보정
# =========================================================
def ensure_formula_schema(df: pd.DataFrame, beverage_type: str) -> pd.DataFrame:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame(columns=[
            "Ingredient_Name", "Category", "Ingredient_Role",
            "Brix", "pH", "Acidity", "Sweetness", "Cost",
            "Brix_Contribution", "Acid_Contribution", "pH_Effect",
            "Typical_Range_Min", "Typical_Range_Max",
            "FlavorContribution", "Purpose", "Usage_%"
        ])

    df = normalize_columns(df.copy())

    defaults = {
        "Ingredient_Name": "",
        "Category": "",
        "Ingredient_Role": "",
        "Brix": 0.0,
        "pH": 7.0,
        "Acidity": 0.0,
        "Sweetness": 0.0,
        "Cost": 0.0,
        "Brix_Contribution": 0.0,
        "Acid_Contribution": 0.0,
        "pH_Effect": 0.0,
        "Typical_Range_Min": 0.0,
        "Typical_Range_Max": 0.0,
        "FlavorContribution": 0.0,
        "Purpose": "",
        "Usage_%": 0.0,
    }

    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default

    df = enforce_numeric(df, [
        "Brix", "pH", "Acidity", "Sweetness", "Cost",
        "Brix_Contribution", "Acid_Contribution", "pH_Effect",
        "Typical_Range_Min", "Typical_Range_Max",
        "FlavorContribution", "Usage_%"
    ])

    # Role 추론
    missing_role = df["Ingredient_Role"].astype(str).str.strip() == ""
    if missing_role.any():
        for idx in df[missing_role].index:
            cat = str(df.at[idx, "Category"]).strip()
            inferred = ""
            if cat == "Water":
                inferred = "Water"
            elif cat == "Sugar":
                inferred = "Sugar"
            elif cat == "Sweetener":
                inferred = "Sweetener"
            elif cat == "Acid":
                inferred = "Acid"
            elif cat in ["Concentrate", "Extract"]:
                inferred = "Flavor"
            elif cat == "Stabilizer":
                inferred = "Stabilizer"
            elif cat == "Color":
                inferred = "Color"
            elif cat == "Vitamin":
                inferred = "Vitamin"
            elif cat == "Functional":
                inferred = "Functional"
            elif cat == "Electrolyte":
                inferred = "Electrolyte"
            df.at[idx, "Ingredient_Role"] = inferred

    # 필수 역할 보충
    existing_roles = set(df["Ingredient_Role"].astype(str).tolist())
    for role, (mn, mx) in TYPE_TEMPLATES.get(beverage_type, {}).items():
        if role in existing_roles:
            continue

        auto_row = {
            "Ingredient_Name": f"Auto_{role}",
            "Category": role_to_categories(role)[0] if role_to_categories(role) else role,
            "Ingredient_Role": role,
            "Brix": 0.0,
            "pH": 7.0 if role == "Water" else 4.0,
            "Acidity": 0.0,
            "Sweetness": 0.0,
            "Cost": 0.0,
            "Brix_Contribution": 0.0,
            "Acid_Contribution": 0.0,
            "pH_Effect": 0.0,
            "Typical_Range_Min": mn,
            "Typical_Range_Max": mx,
            "FlavorContribution": 0.0,
            "Purpose": role,
            "Usage_%": 0.0,
        }
        df = pd.concat([df, pd.DataFrame([auto_row])], ignore_index=True)

    return df.reset_index(drop=True)


# =========================================================
# 샘플 데이터
# =========================================================
def build_sample_ingredient_master() -> pd.DataFrame:
    rows = [
        {"Ingredient_ID": 1, "Ingredient_Name": "정제수", "Category": "Water", "Cost": 5},
        {"Ingredient_ID": 2, "Ingredient_Name": "설탕", "Category": "Sugar", "Cost": 1200},
        {"Ingredient_ID": 3, "Ingredient_Name": "액상과당", "Category": "Sugar", "Cost": 900},
        {"Ingredient_ID": 4, "Ingredient_Name": "수크랄로스", "Category": "Sweetener", "Cost": 150000},
        {"Ingredient_ID": 5, "Ingredient_Name": "아세설팜K", "Category": "Sweetener", "Cost": 98000},
        {"Ingredient_ID": 6, "Ingredient_Name": "구연산", "Category": "Acid", "Cost": 3500},
        {"Ingredient_ID": 7, "Ingredient_Name": "사과산", "Category": "Acid", "Cost": 4200},
        {"Ingredient_ID": 8, "Ingredient_Name": "인산", "Category": "Acid", "Cost": 2800},
        {"Ingredient_ID": 9, "Ingredient_Name": "녹차추출물", "Category": "Extract", "Cost": 45000},
        {"Ingredient_ID": 10, "Ingredient_Name": "생강추출물", "Category": "Extract", "Cost": 38000},
        {"Ingredient_ID": 11, "Ingredient_Name": "히비스커스추출물", "Category": "Extract", "Cost": 41000},
        {"Ingredient_ID": 12, "Ingredient_Name": "레몬농축액", "Category": "Concentrate", "Cost": 8000},
        {"Ingredient_ID": 13, "Ingredient_Name": "오렌지농축액", "Category": "Concentrate", "Cost": 7000},
        {"Ingredient_ID": 14, "Ingredient_Name": "사과농축액", "Category": "Concentrate", "Cost": 6500},
        {"Ingredient_ID": 15, "Ingredient_Name": "망고농축액", "Category": "Concentrate", "Cost": 8200},
        {"Ingredient_ID": 16, "Ingredient_Name": "복숭아농축액", "Category": "Concentrate", "Cost": 7800},
        {"Ingredient_ID": 17, "Ingredient_Name": "포도농축액", "Category": "Concentrate", "Cost": 7200},
        {"Ingredient_ID": 18, "Ingredient_Name": "파인애플농축액", "Category": "Concentrate", "Cost": 7500},
        {"Ingredient_ID": 19, "Ingredient_Name": "펙틴", "Category": "Stabilizer", "Cost": 22000},
        {"Ingredient_ID": 20, "Ingredient_Name": "잔탄검", "Category": "Stabilizer", "Cost": 18000},
        {"Ingredient_ID": 21, "Ingredient_Name": "카라멜색소", "Category": "Color", "Cost": 6000},
        {"Ingredient_ID": 22, "Ingredient_Name": "베타카로틴", "Category": "Color", "Cost": 50000},
        {"Ingredient_ID": 23, "Ingredient_Name": "비타민C", "Category": "Vitamin", "Cost": 15000},
        {"Ingredient_ID": 24, "Ingredient_Name": "비타민B군믹스", "Category": "Vitamin", "Cost": 30000},
        {"Ingredient_ID": 25, "Ingredient_Name": "타우린", "Category": "Functional", "Cost": 18000},
        {"Ingredient_ID": 26, "Ingredient_Name": "카페인", "Category": "Functional", "Cost": 95000},
        {"Ingredient_ID": 27, "Ingredient_Name": "L-카르니틴", "Category": "Functional", "Cost": 65000},
        {"Ingredient_ID": 28, "Ingredient_Name": "염화나트륨", "Category": "Electrolyte", "Cost": 800},
        {"Ingredient_ID": 29, "Ingredient_Name": "염화칼륨", "Category": "Electrolyte", "Cost": 2500},
    ]
    return pd.DataFrame(rows)


def build_sample_ingredient_property() -> pd.DataFrame:
    rows = [
        {"Ingredient_ID": 1, "Brix": 0.0, "pH": 7.0, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0},
        {"Ingredient_ID": 2, "Brix": 100.0, "pH": 7.0, "Acidity": 0.0, "Sweetness": 1.0, "Brix_Contribution": 1.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0},
        {"Ingredient_ID": 3, "Brix": 77.0, "pH": 6.5, "Acidity": 0.0, "Sweetness": 1.1, "Brix_Contribution": 0.77, "Acid_Contribution": 0.0, "pH_Effect": 0.0},
        {"Ingredient_ID": 4, "Brix": 0.0, "pH": 6.0, "Acidity": 0.0, "Sweetness": 600.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0},
        {"Ingredient_ID": 5, "Brix": 0.0, "pH": 6.0, "Acidity": 0.0, "Sweetness": 200.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0},
        {"Ingredient_ID": 6, "Brix": 0.0, "pH": 2.2, "Acidity": 100.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 1.0, "pH_Effect": -0.30},
        {"Ingredient_ID": 7, "Brix": 0.0, "pH": 2.6, "Acidity": 100.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 1.0, "pH_Effect": -0.25},
        {"Ingredient_ID": 8, "Brix": 0.0, "pH": 1.8, "Acidity": 85.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.85, "pH_Effect": -0.35},
        {"Ingredient_ID": 9, "Brix": 2.0, "pH": 5.8, "Acidity": 0.2, "Sweetness": 0.1, "Brix_Contribution": 0.02, "Acid_Contribution": 0.002, "pH_Effect": -0.002},
        {"Ingredient_ID": 10, "Brix": 4.0, "pH": 5.2, "Acidity": 0.3, "Sweetness": 0.1, "Brix_Contribution": 0.04, "Acid_Contribution": 0.003, "pH_Effect": -0.003},
        {"Ingredient_ID": 11, "Brix": 3.0, "pH": 3.1, "Acidity": 0.8, "Sweetness": 0.2, "Brix_Contribution": 0.03, "Acid_Contribution": 0.008, "pH_Effect": -0.010},
        {"Ingredient_ID": 12, "Brix": 65.0, "pH": 2.2, "Acidity": 6.5, "Sweetness": 0.8, "Brix_Contribution": 0.65, "Acid_Contribution": 0.065, "pH_Effect": -0.060},
        {"Ingredient_ID": 13, "Brix": 65.0, "pH": 3.2, "Acidity": 1.2, "Sweetness": 0.9, "Brix_Contribution": 0.65, "Acid_Contribution": 0.012, "pH_Effect": -0.012},
        {"Ingredient_ID": 14, "Brix": 70.0, "pH": 3.5, "Acidity": 0.8, "Sweetness": 0.9, "Brix_Contribution": 0.70, "Acid_Contribution": 0.008, "pH_Effect": -0.008},
        {"Ingredient_ID": 15, "Brix": 65.0, "pH": 3.6, "Acidity": 0.9, "Sweetness": 1.0, "Brix_Contribution": 0.65, "Acid_Contribution": 0.009, "pH_Effect": -0.009},
        {"Ingredient_ID": 16, "Brix": 66.0, "pH": 3.5, "Acidity": 0.7, "Sweetness": 0.9, "Brix_Contribution": 0.66, "Acid_Contribution": 0.007, "pH_Effect": -0.007},
        {"Ingredient_ID": 17, "Brix": 68.0, "pH": 3.4, "Acidity": 0.7, "Sweetness": 0.8, "Brix_Contribution": 0.68, "Acid_Contribution": 0.007, "pH_Effect": -0.007},
        {"Ingredient_ID": 18, "Brix": 60.0, "pH": 3.3, "Acidity": 1.5, "Sweetness": 0.9, "Brix_Contribution": 0.60, "Acid_Contribution": 0.015, "pH_Effect": -0.015},
        {"Ingredient_ID": 19, "Brix": 0.0, "pH": 4.0, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0},
        {"Ingredient_ID": 20, "Brix": 0.0, "pH": 6.0, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0},
        {"Ingredient_ID": 21, "Brix": 0.0, "pH": 4.0, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0},
        {"Ingredient_ID": 22, "Brix": 0.0, "pH": 6.0, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0},
        {"Ingredient_ID": 23, "Brix": 0.0, "pH": 2.4, "Acidity": 100.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 1.0, "pH_Effect": -0.26},
        {"Ingredient_ID": 24, "Brix": 0.0, "pH": 5.0, "Acidity": 0.2, "Sweetness": 0.1, "Brix_Contribution": 0.0, "Acid_Contribution": 0.002, "pH_Effect": -0.002},
        {"Ingredient_ID": 25, "Brix": 0.0, "pH": 6.0, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0},
        {"Ingredient_ID": 26, "Brix": 0.0, "pH": 6.5, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0},
        {"Ingredient_ID": 27, "Brix": 0.0, "pH": 6.5, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0},
        {"Ingredient_ID": 28, "Brix": 0.0, "pH": 7.0, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0},
        {"Ingredient_ID": 29, "Brix": 0.0, "pH": 7.0, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0},
    ]
    return pd.DataFrame(rows)


def build_sample_flavor_map() -> pd.DataFrame:
    rows = []
    for bev_type, flavors in TREND_FLAVORS.items():
        for flavor in flavors:
            fl = flavor.lower()
            base = [
                ("정제수", "Water", 70.0, 95.0, "Base"),
                ("설탕", "Sugar", 0.0, 12.0, "Sweetness"),
                ("수크랄로스", "Sweetener", 0.0, 0.03, "Sweetness"),
                ("구연산", "Acid", 0.05, 0.30, "Acidity"),
                ("펙틴", "Stabilizer", 0.0, 0.20, "Stability"),
            ]
            if any(k in fl for k in ["lemon", "lime", "yuzu", "citrus"]):
                base += [("레몬농축액", "Flavor", 0.30, 12.0, "Flavor")]
            if any(k in fl for k in ["orange", "grapefruit"]):
                base += [("오렌지농축액", "Flavor", 0.30, 15.0, "Flavor")]
            if "apple" in fl:
                base += [("사과농축액", "Flavor", 0.30, 15.0, "Flavor")]
            if any(k in fl for k in ["mango", "tropical"]):
                base += [("망고농축액", "Flavor", 0.30, 18.0, "Flavor")]
            if "peach" in fl:
                base += [("복숭아농축액", "Flavor", 0.30, 15.0, "Flavor")]
            if any(k in fl for k in ["berry", "grape", "hibiscus", "pomegranate"]):
                base += [("포도농축액", "Flavor", 0.30, 15.0, "Flavor"), ("히비스커스추출물", "Flavor", 0.02, 0.30, "Flavor")]
            if "pineapple" in fl:
                base += [("파인애플농축액", "Flavor", 0.30, 15.0, "Flavor")]
            if "ginger" in fl:
                base += [("생강추출물", "Flavor", 0.01, 0.20, "Flavor")]
            if "matcha" in fl:
                base += [("녹차추출물", "Flavor", 0.05, 0.30, "Flavor")]
            if bev_type == "스포츠음료":
                base += [("염화나트륨", "Electrolyte", 0.05, 0.20, "Electrolyte"), ("염화칼륨", "Electrolyte", 0.01, 0.10, "Electrolyte")]
            if bev_type == "에너지음료":
                base += [("타우린", "Functional", 0.20, 0.40, "Energy"), ("카페인", "Functional", 0.01, 0.04, "Energy"), ("비타민B군믹스", "Vitamin", 0.01, 0.05, "Vitamin")]
            if bev_type == "기능성음료":
                base += [("비타민C", "Vitamin", 0.02, 0.10, "Function")]
            if bev_type == "식물성음료":
                base += [("잔탄검", "Stabilizer", 0.05, 0.20, "Mouthfeel")]
            if bev_type == "탄산음료":
                base += [("카라멜색소", "Color", 0.0, 0.01, "Color")]

            for ing_name, role, mn, mx, func in base:
                rows.append({
                    "Beverage_Type": bev_type,
                    "Flavor": flavor,
                    "Ingredient_Name": ing_name,
                    "Ingredient_Role": role,
                    "Typical_Range_Min": mn,
                    "Typical_Range_Max": mx,
                    "Function": func,
                })
    return pd.DataFrame(rows)


# =========================================================
# 로드
# =========================================================
@st.cache_data(show_spinner=False)
def load_or_build_db() -> Dict[str, pd.DataFrame]:
    master = normalize_columns(build_sample_ingredient_master())
    prop = normalize_columns(build_sample_ingredient_property())
    flavor_map = normalize_columns(build_sample_flavor_map())

    if os.path.exists(DEFAULT_EXCEL_PATH):
        try:
            xls = pd.ExcelFile(DEFAULT_EXCEL_PATH)
            for sheet in xls.sheet_names:
                try:
                    df = normalize_columns(pd.read_excel(xls, sheet_name=sheet))
                    cols = set(df.columns)
                    if {"Ingredient_ID", "Ingredient_Name", "Category"}.issubset(cols):
                        master = df
                    elif {"Ingredient_ID", "Brix", "pH"}.issubset(cols):
                        prop = df
                except Exception:
                    pass
        except Exception:
            pass

    master = enforce_numeric(master, ["Ingredient_ID", "Cost"])
    prop = enforce_numeric(prop, [
        "Ingredient_ID", "Brix", "pH", "Acidity", "Sweetness",
        "Brix_Contribution", "Acid_Contribution", "pH_Effect"
    ])

    return {
        "Ingredient_Master": master,
        "Ingredient_Property": prop,
        "Flavor_Ingredient_Map": flavor_map,
    }


def merge_ingredient_data(master_df: pd.DataFrame, prop_df: pd.DataFrame) -> pd.DataFrame:
    df = pd.merge(master_df, prop_df, on="Ingredient_ID", how="left")
    return ensure_formula_schema(df, "탄산음료")


# =========================================================
# 핵심 로직
# =========================================================
def build_random_recommendations(beverage_type: str, n: int = 10) -> List[str]:
    pool = TREND_FLAVORS.get(beverage_type, [])
    if not pool:
        return []
    return random.sample(pool, min(n, len(pool)))


def recommendation_reason(beverage_type: str, flavor_name: str) -> str:
    fl = flavor_name.lower()
    reasons = []

    base = {
        "탄산음료": "청량감과 첫 향 인지가 중요한 유형이라 임팩트 있는 풍미가 유리함",
        "과채음료": "과즙감·자연스러움·컬러 스토리텔링이 쉬운 flavor",
        "스포츠음료": "가볍고 상쾌한 향이라 전해질 음료에 적용성이 높음",
        "에너지음료": "강한 첫인상과 기능성 이미지를 동시에 줄 수 있음",
        "식물성음료": "부드러운 바디감과 결합하기 쉬운 풍미 방향",
        "기능성음료": "기능성 원료의 이취를 완화하고 건강 이미지를 강화하기 쉬움",
    }
    reasons.append(base.get(beverage_type, "유형 적합성이 높음"))

    if any(k in fl for k in ["lemon", "lime", "yuzu", "citrus", "orange", "grapefruit"]):
        reasons.append("시트러스 계열이라 산미와 향 발현 설계가 직관적임")
    if any(k in fl for k in ["mango", "pineapple", "guava", "passionfruit", "tropical"]):
        reasons.append("트로피컬 계열이라 시각적 임팩트와 트렌드성이 큼")
    if any(k in fl for k in ["berry", "grape", "hibiscus", "pomegranate", "lychee"]):
        reasons.append("컬러감과 프리미엄 포지셔닝에 유리함")
    if any(k in fl for k in ["ginger", "mint", "cucumber"]):
        reasons.append("차별화 포인트가 분명해 신제품화가 쉬움")
    if any(k in fl for k in ["vanilla", "chocolate", "banana", "matcha", "coffee"]):
        reasons.append("부드러운 바디감 또는 디저트형 콘셉트와 잘 연결됨")

    return " / ".join(reasons[:3])


def build_ai_ingredient_view(
    ingredient_df: pd.DataFrame,
    flavor_map_df: pd.DataFrame,
    beverage_type: str,
    flavor_name: str,
    client,
    model_name: str,
) -> pd.DataFrame:
    matched = flavor_map_df[
        (flavor_map_df["Beverage_Type"] == beverage_type) &
        (flavor_map_df["Flavor"].astype(str).str.lower() == flavor_name.lower())
    ].copy()

    rule_df = ingredient_df.merge(
        matched[["Ingredient_Name", "Ingredient_Role", "Typical_Range_Min", "Typical_Range_Max", "Function"]],
        on="Ingredient_Name",
        how="inner",
    )

    rule_df = ensure_formula_schema(rule_df, beverage_type)
    rule_df["Source"] = "Rule-Based"
    return rule_df


def build_standard_formula_from_intensity(
    filtered_df: pd.DataFrame,
    beverage_type: str,
    ph_intensity: int,
    acid_intensity: int,
    sweet_intensity: int,
) -> pd.DataFrame:
    filtered_df = ensure_formula_schema(filtered_df, beverage_type)

    template = TYPE_TEMPLATES.get(beverage_type, {})
    rows = []

    role_target_map = {}
    for role, (low, high) in template.items():
        if role in ["Sugar", "Sweetener"]:
            role_target_map[role] = map_intensity_to_value(sweet_intensity, low, high)
        elif role == "Acid":
            role_target_map[role] = map_intensity_to_value(acid_intensity, low, high)
        elif role in ["Flavor", "Concentrate", "Extract"]:
            role_target_map[role] = round((low + high) / 2.0, 4)
        else:
            role_target_map[role] = round((low + high) / 2.0, 4)

    for role in template.keys():
        candidates = filtered_df[filtered_df["Ingredient_Role"] == role].copy()
        if candidates.empty:
            candidates = filtered_df[filtered_df["Category"].isin(role_to_categories(role))].copy()

        if candidates.empty and role != "Water":
            continue

        if role == "Water":
            rows.append({
                "Ingredient_Name": "정제수",
                "Category": "Water",
                "Ingredient_Role": "Water",
                "Brix": 0.0,
                "pH": 7.0,
                "Acidity": 0.0,
                "Sweetness": 0.0,
                "Cost": 5.0,
                "Brix_Contribution": 0.0,
                "Acid_Contribution": 0.0,
                "pH_Effect": 0.0,
                "Purpose": "Base",
                "Usage_%": 0.0,
            })
            continue

        chosen = candidates.iloc[0].to_dict()
        chosen["Usage_%"] = role_target_map[role]
        rows.append(chosen)

    formula_df = pd.DataFrame(rows)
    formula_df = rebalance_water(formula_df)

    if not formula_df.empty and ph_intensity != 3:
        ph_multiplier = {1: 0.80, 2: 0.92, 3: 1.00, 4: 1.10, 5: 1.18}[ph_intensity]
        acid_like = formula_df["Ingredient_Role"].isin(["Acid", "Flavor", "Concentrate", "Extract"])
        formula_df.loc[acid_like, "Usage_%"] = formula_df.loc[acid_like, "Usage_%"] * ph_multiplier
        formula_df = rebalance_water(formula_df)

    return ensure_formula_schema(formula_df, beverage_type)


def rebalance_water(formula_df: pd.DataFrame) -> pd.DataFrame:
    df = formula_df.copy()
    df["Usage_%"] = pd.to_numeric(df["Usage_%"], errors="coerce").fillna(0.0)
    non_water_sum = df.loc[df["Ingredient_Role"] != "Water", "Usage_%"].sum()
    water_value = round(max(0.0, 100.0 - non_water_sum), 4)

    water_idx = df.index[df["Ingredient_Role"] == "Water"].tolist()
    if water_idx:
        df.loc[water_idx[0], "Usage_%"] = water_value
    else:
        water_row = {
            "Ingredient_Name": "정제수",
            "Category": "Water",
            "Ingredient_Role": "Water",
            "Brix": 0.0,
            "pH": 7.0,
            "Acidity": 0.0,
            "Sweetness": 0.0,
            "Cost": 5.0,
            "Brix_Contribution": 0.0,
            "Acid_Contribution": 0.0,
            "pH_Effect": 0.0,
            "Purpose": "Base",
            "Usage_%": water_value,
        }
        df = pd.concat([pd.DataFrame([water_row]), df], ignore_index=True)
    return df


def calculate_properties(formula_df: pd.DataFrame, beverage_type: str) -> FormulaSummary:
    df = ensure_formula_schema(formula_df, beverage_type)
    if df.empty:
        return FormulaSummary(0.0, 0.0, 0.0, 0.0, 7.0, 999999.0)

    df["Brix_Contribution_Value"] = df["Usage_%"] * df["Brix"] / 100.0
    df["Acid_Contribution_Value"] = df["Usage_%"] * df["Acidity"] / 100.0
    df["Sweetness_Contribution_Value"] = df["Usage_%"] * df["Sweetness"] / 100.0
    df["Cost_Contribution"] = df["Usage_%"] * df["Cost"] / 100.0

    total_brix = round(df["Brix_Contribution_Value"].sum(), 4)
    total_acid = round(df["Acid_Contribution_Value"].sum(), 4)
    total_sweetness = round(df["Sweetness_Contribution_Value"].sum(), 4)
    total_cost = round(df["Cost_Contribution"].sum(), 4)

    base_ph = 6.8 if beverage_type == "식물성음료" else 4.2
    total_ph = round(clamp(base_ph + (df["pH_Effect"] * df["Usage_%"]).sum(), 1.5, 8.0), 4)

    return FormulaSummary(total_brix, total_acid, total_sweetness, total_cost, total_ph, 0.0)


def create_individual(filtered_df: pd.DataFrame, beverage_type: str) -> pd.DataFrame:
    filtered_df = ensure_formula_schema(filtered_df, beverage_type)

    template = TYPE_TEMPLATES.get(beverage_type, {})
    rows = []

    for role, (low, high) in template.items():
        candidates = filtered_df[filtered_df["Ingredient_Role"] == role].copy()
        if candidates.empty:
            candidates = filtered_df[filtered_df["Category"].isin(role_to_categories(role))].copy()

        if candidates.empty and role != "Water":
            continue

        if role == "Water":
            rows.append({
                "Ingredient_Name": "정제수",
                "Category": "Water",
                "Ingredient_Role": "Water",
                "Brix": 0.0,
                "pH": 7.0,
                "Acidity": 0.0,
                "Sweetness": 0.0,
                "Cost": 5.0,
                "Brix_Contribution": 0.0,
                "Acid_Contribution": 0.0,
                "pH_Effect": 0.0,
                "Purpose": "Base",
                "Usage_%": 0.0,
            })
            continue

        chosen = candidates.sample(1, random_state=random.randint(1, 100000)).iloc[0].to_dict()
        chosen["Usage_%"] = round(random.uniform(low, high), 4)
        rows.append(chosen)

    return ensure_formula_schema(rebalance_water(pd.DataFrame(rows)), beverage_type)


def evaluate(
    formula_df: pd.DataFrame,
    beverage_type: str,
    target_brix: float,
    target_sweetness: float,
    target_acidity: float,
) -> Tuple[float, FormulaSummary]:
    summary = calculate_properties(formula_df, beverage_type)
    score = (
        abs(target_brix - summary.total_brix) * 40.0
        + abs(target_acidity - summary.total_acid) * 60.0
        + abs(target_sweetness - summary.total_sweetness) * 30.0
        + summary.total_cost * 0.01
    )
    summary.score = round(score, 4)
    return score, summary


def crossover(parent1: pd.DataFrame, parent2: pd.DataFrame, beverage_type: str) -> pd.DataFrame:
    parent1 = ensure_formula_schema(parent1, beverage_type)
    parent2 = ensure_formula_schema(parent2, beverage_type)

    roles = sorted(set(parent1["Ingredient_Role"].tolist()) | set(parent2["Ingredient_Role"].tolist()))
    rows = []
    for role in roles:
        source = parent1 if random.random() < 0.5 else parent2
        candidates = source[source["Ingredient_Role"] == role]
        if not candidates.empty:
            rows.append(candidates.iloc[0].to_dict())

    return ensure_formula_schema(rebalance_water(pd.DataFrame(rows)), beverage_type)


def mutate(formula_df: pd.DataFrame, beverage_type: str, mutation_rate: float = 0.20) -> pd.DataFrame:
    df = ensure_formula_schema(formula_df, beverage_type)
    template = TYPE_TEMPLATES.get(beverage_type, {})

    for idx, row in df.iterrows():
        role = row.get("Ingredient_Role", "")
        if role == "Water":
            continue
        if random.random() < mutation_rate and role in template:
            low, high = template[role]
            df.at[idx, "Usage_%"] = round(random.uniform(low, high), 4)

    return ensure_formula_schema(rebalance_water(df), beverage_type)


def optimize_formula(
    filtered_df: pd.DataFrame,
    beverage_type: str,
    target_brix: float,
    target_sweetness: float,
    target_acidity: float,
    population_size: int,
    generations: int,
) -> List[Tuple[pd.DataFrame, FormulaSummary]]:
    filtered_df = ensure_formula_schema(filtered_df, beverage_type)
    population = []

    for _ in range(max(20, population_size)):
        indiv = create_individual(filtered_df, beverage_type)
        _, summary = evaluate(indiv, beverage_type, target_brix, target_sweetness, target_acidity)
        population.append((indiv, summary))

    for _ in range(max(1, generations)):
        population = sorted(population, key=lambda x: x[1].score)
        survivors = population[:max(4, int(len(population) * 0.3))]

        new_population = survivors.copy()
        while len(new_population) < population_size:
            p1 = random.choice(survivors)[0]
            p2 = random.choice(survivors)[0]
            child = crossover(p1, p2, beverage_type)
            child = mutate(child, beverage_type, mutation_rate=0.20)
            _, child_summary = evaluate(child, beverage_type, target_brix, target_sweetness, target_acidity)
            new_population.append((child, child_summary))

        population = new_population

    return sorted(population, key=lambda x: x[1].score)[:20]


# =========================================================
# 출력 / 검증 / 보고서
# =========================================================
def validate_formula(summary: FormulaSummary, beverage_type: str) -> Tuple[str, Dict[str, str]]:
    rule = VALIDATION_RANGES.get(beverage_type)
    if not rule:
        return "UNKNOWN", {}

    details = {}
    passed = True
    for metric, (low, high) in rule.items():
        val = summary.total_brix if metric == "Brix" else summary.total_ph if metric == "pH" else summary.total_acid
        ok = low <= val <= high
        details[metric] = f"{val:.4f} / 기준 {low}~{high} / {'PASS' if ok else 'FAIL'}"
        if not ok:
            passed = False
    return ("PASS" if passed else "FAIL"), details


def render_formula_table(formula_df: pd.DataFrame, beverage_type: str) -> pd.DataFrame:
    df = ensure_formula_schema(formula_df, beverage_type)
    if df.empty:
        return df

    summary = calculate_properties(df, beverage_type)

    df["Brix_Contribution_Value"] = df["Usage_%"] * df["Brix"] / 100.0
    df["Acid_Contribution_Value"] = df["Usage_%"] * df["Acidity"] / 100.0
    df["Sweetness_Contribution_Value"] = df["Usage_%"] * df["Sweetness"] / 100.0
    df["Cost_Contribution"] = df["Usage_%"] * df["Cost"] / 100.0

    display_cols = [
        "Ingredient_Name", "Category", "Ingredient_Role", "Usage_%", "Cost",
        "Cost_Contribution", "Brix", "Brix_Contribution_Value", "pH",
        "Acidity", "Acid_Contribution_Value", "Sweetness",
        "Sweetness_Contribution_Value", "FlavorContribution", "Purpose"
    ]
    out = df[display_cols].copy()

    total_row = pd.DataFrame([{
        "Ingredient_Name": "TOTAL",
        "Category": "-",
        "Ingredient_Role": "-",
        "Usage_%": round(pd.to_numeric(out["Usage_%"], errors="coerce").fillna(0.0).sum(), 4),
        "Cost": "",
        "Cost_Contribution": round(summary.total_cost, 4),
        "Brix": "",
        "Brix_Contribution_Value": round(summary.total_brix, 4),
        "pH": round(summary.total_ph, 4),
        "Acidity": "",
        "Acid_Contribution_Value": round(summary.total_acid, 4),
        "Sweetness": "",
        "Sweetness_Contribution_Value": round(summary.total_sweetness, 4),
        "FlavorContribution": "",
        "Purpose": f"Score={summary.score:.4f}",
    }])

    return pd.concat([out, total_row], ignore_index=True)


def fallback_multi_report(beverage_type: str, flavor_name: str, summary: FormulaSummary, validation_status: str) -> str:
    if summary.total_brix < 5:
        sweet_comment = "감미가 약한 편이라 대중성 확보를 위해 당류 또는 고감미료 보정이 필요하다."
    elif summary.total_brix > 13:
        sweet_comment = "당도 체감이 높아 후미와 음용 피로도를 점검해야 한다."
    else:
        sweet_comment = "감미 밸런스는 안정적인 편이다."

    if summary.total_acid < 0.08:
        acid_comment = "산미가 약해 향의 입체감이 부족할 수 있다."
    elif summary.total_acid > 0.30:
        acid_comment = "산미가 강해 자극감이 커질 수 있다."
    else:
        acid_comment = "산미 수준은 대체로 적정하다."

    return f"""
1. 기술 평가 보고서
- 제품유형: {beverage_type}
- 제품명/Flavor: {flavor_name}
- Brix {summary.total_brix:.4f}, pH {summary.total_ph:.4f}, Acid {summary.total_acid:.4f}, Sweetness {summary.total_sweetness:.4f} 수준이다.
- {sweet_comment}
- {acid_comment}

2. 마케팅 평가 보고서
- {flavor_name}는 {beverage_type} 카테고리에서 시각적 연상성과 전달력이 높다.
- 제품명만으로도 flavor 콘셉트가 비교적 직관적으로 전달된다.
- 프리미엄 또는 트렌디 포지셔닝이 가능하다.

3. 토의 결과 요약
- 연구원 관점: 표준배합 범위 내 물성 안정성과 원가가 중요하다.
- 마케팅 관점: 첫인상, 제품명 전달력, 컬러 스토리텔링이 중요하다.
- 종합 판정: 현재 배합은 {validation_status} 수준이며, 미세 조정 후 시제품화 가치가 있다.

4. 개선의견 보고서
- 핵심 농축액/추출물 상위 1~2개 비율을 조정해 풍미 선명도를 높일 것
- 산미와 감미 밸런스를 재조정해 음용성을 강화할 것
- 원가가 높은 기능성 원료는 메시지 유지 범위에서 최소 유효량 최적화가 필요하다

5. 최종 권고안
- 1차 관능평가를 진행하고, 그 결과를 반영해 Brix / Acid / Flavor 비율을 재세팅하는 것을 권장한다.
""".strip()


def generate_image_with_openai(client, prompt: str, model_name: str = "gpt-image-1") -> Optional[bytes]:
    try:
        response = client.images.generate(
            model=model_name,
            prompt=prompt,
            size="1024x1024",
            quality="high",
        )
        if hasattr(response, "data") and response.data:
            item = response.data[0]
            if getattr(item, "b64_json", None):
                return base64.b64decode(item.b64_json)
        return None
    except Exception:
        return None


def build_image_prompt(product_name: str, beverage_type: str, formula_df: pd.DataFrame) -> str:
    df = ensure_formula_schema(formula_df, beverage_type)
    top_ings = (
        df[df["Ingredient_Role"] != "Water"]
        .sort_values("Usage_%", ascending=False)
        .head(6)["Ingredient_Name"]
        .astype(str)
        .tolist()
    )
    ing_text = ", ".join(top_ings)

    return f"""
Create a premium commercial beverage product image.
Product name: {product_name}
Beverage type: {beverage_type}
Key ingredients: {ing_text}
Mood: futuristic food research lab, automated robotic beverage development center
Style: photorealistic, premium package hero shot, Korean retail market, high detail
""".strip()


def to_excel_bytes(formula_table: pd.DataFrame, ingredient_db_view: pd.DataFrame, summary: FormulaSummary, validation_status: str, validation_details: Dict[str, str]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        formula_table.to_excel(writer, sheet_name="Formula", index=False)
        ingredient_db_view.to_excel(writer, sheet_name="Ingredient_DB", index=False)
        pd.DataFrame([{
            "Brix": summary.total_brix,
            "pH": summary.total_ph,
            "Acid": summary.total_acid,
            "Sweetness": summary.total_sweetness,
            "Cost": summary.total_cost,
            "Score": summary.score,
            "Validation": validation_status,
        }]).to_excel(writer, sheet_name="Summary", index=False)
        if validation_details:
            pd.DataFrame([{"Metric": k, "Detail": v} for k, v in validation_details.items()]).to_excel(
                writer, sheet_name="Validation", index=False
            )
    output.seek(0)
    return output.read()


# =========================================================
# 데이터 준비
# =========================================================
db = load_or_build_db()
master_df = db["Ingredient_Master"]
prop_df = db["Ingredient_Property"]
flavor_map_df = db["Flavor_Ingredient_Map"]
ingredient_df = merge_ingredient_data(master_df, prop_df)

# =========================================================
# 세션
# =========================================================
if "last_beverage_type" not in st.session_state:
    st.session_state.last_beverage_type = UI_BEVERAGE_TYPES[0]
if "recommended_flavors" not in st.session_state:
    st.session_state.recommended_flavors = build_random_recommendations(UI_BEVERAGE_TYPES[0], 10)
if "selected_flavor" not in st.session_state:
    st.session_state.selected_flavor = st.session_state.recommended_flavors[0]
if "ph_intensity" not in st.session_state:
    st.session_state.ph_intensity = 3
if "acid_intensity" not in st.session_state:
    st.session_state.acid_intensity = 3
if "sweet_intensity" not in st.session_state:
    st.session_state.sweet_intensity = 3

# =========================================================
# 사이드바
# =========================================================
with st.sidebar:
    st.markdown("### 🕹️ 조종실 제어 패널")
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    model_name = st.text_input("Text Model", value="gpt-5.4")
    image_model_name = st.text_input("Image Model", value="gpt-image-1")

    st.markdown("---")
    beverage_type = st.selectbox("🥤 음료 유형", UI_BEVERAGE_TYPES)

    if beverage_type != st.session_state.last_beverage_type:
        st.session_state.last_beverage_type = beverage_type
        st.session_state.recommended_flavors = build_random_recommendations(beverage_type, 10)
        st.session_state.selected_flavor = st.session_state.recommended_flavors[0]
        st.session_state.ph_intensity = 3
        st.session_state.acid_intensity = 3
        st.session_state.sweet_intensity = 3

    selected_flavor = st.selectbox(
        "🧪 제품명 / Flavor",
        st.session_state.recommended_flavors,
        key="selected_flavor",
    )

    st.markdown("#### 표준 강도 조절")
    ph_intensity = st.select_slider(
        "표준 pH 강도",
        options=[1, 2, 3, 4, 5],
        format_func=lambda x: INTENSITY_LABELS[x],
        key="ph_intensity",
    )
    acid_intensity = st.select_slider(
        "표준 Acid 강도",
        options=[1, 2, 3, 4, 5],
        format_func=lambda x: INTENSITY_LABELS[x],
        key="acid_intensity",
    )
    sweet_intensity = st.select_slider(
        "표준 Sweetness 강도",
        options=[1, 2, 3, 4, 5],
        format_func=lambda x: INTENSITY_LABELS[x],
        key="sweet_intensity",
    )

    st.markdown("#### 최적화 제어")
    population_size = st.slider("Population Size", 50, 800, 200, 10)
    generations = st.slider("Generations", 5, 80, 20, 1)

    run_generate = st.button("🤖 자동 배합 생성", use_container_width=True)
    run_image = st.button("🖼️ 제품 이미지 출력", use_container_width=True)

client, client_error = get_openai_client(api_key)

# =========================================================
# 추천
# =========================================================
st.markdown('<div class="panel"><div class="panel-title">🎯 랜덤 트렌드 추천 10선</div>', unsafe_allow_html=True)
for flavor in st.session_state.recommended_flavors:
    st.markdown(
        f'<div class="reason-box"><b>{flavor}</b><br>{recommendation_reason(beverage_type, flavor)}</div>',
        unsafe_allow_html=True,
    )
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 원재료 DB
# =========================================================
ingredient_db_view = build_ai_ingredient_view(
    ingredient_df=ingredient_df,
    flavor_map_df=flavor_map_df,
    beverage_type=beverage_type,
    flavor_name=selected_flavor,
    client=client,
    model_name=model_name,
)
ingredient_db_view = ensure_formula_schema(ingredient_db_view, beverage_type)

st.markdown('<div class="panel"><div class="panel-title">🧬 원재료 DB 상태</div>', unsafe_allow_html=True)
st.dataframe(
    ingredient_db_view[[
        "Ingredient_Name", "Category", "Ingredient_Role",
        "Brix", "pH", "Acidity", "Sweetness", "Cost",
        "Brix_Contribution", "Acid_Contribution", "pH_Effect",
        "Typical_Range_Min", "Typical_Range_Max", "Purpose"
    ]],
    use_container_width=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 표준배합
# =========================================================
std_formula = build_standard_formula_from_intensity(
    filtered_df=ingredient_db_view,
    beverage_type=beverage_type,
    ph_intensity=ph_intensity,
    acid_intensity=acid_intensity,
    sweet_intensity=sweet_intensity,
)
std_summary = calculate_properties(std_formula, beverage_type)

st.markdown('<div class="panel"><div class="panel-title">📐 표준배합비 참고 템플릿</div>', unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="cockpit">
      <div class="cockpit-box"><div class="cockpit-label">표준 Brix</div><div class="cockpit-value">{std_summary.total_brix:.4f}</div></div>
      <div class="cockpit-box"><div class="cockpit-label">표준 pH</div><div class="cockpit-value">{std_summary.total_ph:.4f}</div></div>
      <div class="cockpit-box"><div class="cockpit-label">표준 Acid</div><div class="cockpit-value">{std_summary.total_acid:.4f}</div></div>
      <div class="cockpit-box"><div class="cockpit-label">표준 Sweetness</div><div class="cockpit-value">{std_summary.total_sweetness:.4f}</div></div>
      <div class="cockpit-box"><div class="cockpit-label">표준 Cost</div><div class="cockpit-value">{std_summary.total_cost:.4f}</div></div>
      <div class="cockpit-box"><div class="cockpit-label">강도 설정</div><div class="cockpit-value">{INTENSITY_LABELS[ph_intensity]} / {INTENSITY_LABELS[acid_intensity]} / {INTENSITY_LABELS[sweet_intensity]}</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.dataframe(render_formula_table(std_formula, beverage_type), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

target_brix = std_summary.total_brix
target_sweetness = std_summary.total_sweetness
target_acidity = std_summary.total_acid

# =========================================================
# 자동 배합
# =========================================================
best_formula = None
best_summary = None
formula_table = None
validation_status = None
validation_details = None
report_text = None

if run_generate:
    with st.spinner("조종실 최적화 엔진이 배합비를 계산 중..."):
        top_results = optimize_formula(
            filtered_df=ingredient_db_view,
            beverage_type=beverage_type,
            target_brix=target_brix,
            target_sweetness=target_sweetness,
            target_acidity=target_acidity,
            population_size=population_size,
            generations=generations,
        )

    if top_results:
        summary_rows = []
        for i, (_, summ) in enumerate(top_results, start=1):
            summary_rows.append({
                "Rank": i,
                "Brix": round(summ.total_brix, 4),
                "pH": round(summ.total_ph, 4),
                "Acid": round(summ.total_acid, 4),
                "Sweetness": round(summ.total_sweetness, 4),
                "Cost": round(summ.total_cost, 4),
                "Score": round(summ.score, 4),
            })

        summary_df = pd.DataFrame(summary_rows)
        best_formula, best_summary = top_results[0]
        validation_status, validation_details = validate_formula(best_summary, beverage_type)
        formula_table = render_formula_table(best_formula, beverage_type)

        st.markdown('<div class="panel"><div class="panel-title">🏆 Top 20 자동 배합 결과</div>', unsafe_allow_html=True)
        st.dataframe(summary_df, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel"><div class="panel-title">📋 최종 제품배합비</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="cockpit">
              <div class="cockpit-box"><div class="cockpit-label">Brix</div><div class="cockpit-value">{best_summary.total_brix:.4f}</div></div>
              <div class="cockpit-box"><div class="cockpit-label">pH</div><div class="cockpit-value">{best_summary.total_ph:.4f}</div></div>
              <div class="cockpit-box"><div class="cockpit-label">Acid</div><div class="cockpit-value">{best_summary.total_acid:.4f}</div></div>
              <div class="cockpit-box"><div class="cockpit-label">Sweetness</div><div class="cockpit-value">{best_summary.total_sweetness:.4f}</div></div>
              <div class="cockpit-box"><div class="cockpit-label">Cost</div><div class="cockpit-value">{best_summary.total_cost:.4f}</div></div>
              <div class="cockpit-box"><div class="cockpit-label">Validation</div><div class="cockpit-value">{validation_status}</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(formula_table, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel"><div class="panel-title">✅ 표준배합 검증</div>', unsafe_allow_html=True)
        if validation_details:
            validation_df = pd.DataFrame([{"Metric": k, "Detail": v} for k, v in validation_details.items()])
            st.dataframe(validation_df, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel"><div class="panel-title">📊 결과 분포</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.caption("Brix 분포")
            st.bar_chart(summary_df.set_index("Rank")["Brix"])
        with c2:
            st.caption("원가 분포")
            st.bar_chart(summary_df.set_index("Rank")["Cost"])
        with c3:
            st.caption("Score 분포")
            st.bar_chart(summary_df.set_index("Rank")["Score"])
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel"><div class="panel-title">🧠 평가 및 개선의견 보고서</div>', unsafe_allow_html=True)
        report_text = fallback_multi_report(
            beverage_type=beverage_type,
            flavor_name=selected_flavor,
            summary=best_summary,
            validation_status=validation_status,
        )
        st.text_area("평가 및 개선의견 보고서", value=report_text, height=420)
        st.markdown("</div>", unsafe_allow_html=True)

        csv_data = formula_table.to_csv(index=False).encode("utf-8-sig")
        xlsx_data = to_excel_bytes(
            formula_table=formula_table,
            ingredient_db_view=ingredient_db_view,
            summary=best_summary,
            validation_status=validation_status,
            validation_details=validation_details,
        )

        st.markdown('<div class="panel"><div class="panel-title">⬇️ 다운로드</div>', unsafe_allow_html=True)
        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                "CSV 다운로드",
                data=csv_data,
                file_name=f"formula_{beverage_type}_{selected_flavor.replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with d2:
            st.download_button(
                "Excel 다운로드",
                data=xlsx_data,
                file_name=f"formula_{beverage_type}_{selected_flavor.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 이미지 생성
# =========================================================
st.markdown('<div class="panel"><div class="panel-title">🖼️ 제품 이미지 생성</div>', unsafe_allow_html=True)
if run_image:
    if client is None:
        st.error("이미지 생성을 위해 OpenAI API Key가 필요하다.")
    else:
        current_formula = best_formula if best_formula is not None else std_formula
        image_prompt = build_image_prompt(selected_flavor, beverage_type, current_formula)
        with st.spinner("제품 이미지 생성 중..."):
            image_bytes = generate_image_with_openai(client, image_prompt, image_model_name)
        if image_bytes:
            st.image(image_bytes, caption=f"{selected_flavor} 제품 이미지", use_container_width=True)
        else:
            st.error("이미지 생성에 실패했다. 모델명/API 권한/요청 제한을 확인해라.")
else:
    st.info("제품명 + 배합비 핵심 원료를 조합해 이미지가 생성된다.")
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 디버그
# =========================================================
with st.expander("디버그 / 로드 상태", expanded=False):
    st.write("API Key 입력 여부:", bool(api_key))
    st.write("OpenAI client 상태:", "OK" if client is not None else f"Fallback ({client_error})")
    st.write("기본 엑셀 파일 존재 여부:", os.path.exists(DEFAULT_EXCEL_PATH))
    st.write("Ingredient_Master rows:", len(master_df))
    st.write("Ingredient_Property rows:", len(prop_df))
    st.write("Flavor_Ingredient_Map rows:", len(flavor_map_df))
    st.write("Ingredient columns:", list(ingredient_df.columns))
    st.write("Ingredient DB view rows:", len(ingredient_db_view))
