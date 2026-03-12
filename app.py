import io
import json
import math
import os
import random
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import streamlit as st

# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="AI 음료 신제품 배합비 개발 플랫폼",
    page_icon="🥤",
    layout="wide",
)

# =========================================================
# 상수 / 템플릿
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

# 음료 유형별 표준 템플릿 범위
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
        "Functional": (0.30, 0.60),  # taurine/caffeine/vitamin mix 포함
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

# 검증 기준
VALIDATION_RANGES = {
    "탄산음료": {"Brix": (8.0, 12.0), "pH": (2.5, 4.5), "Acid": (0.10, 0.30)},
    "과채음료": {"Brix": (8.0, 14.0), "pH": (2.5, 4.5), "Acid": (0.10, 0.35)},
    "스포츠음료": {"Brix": (4.0, 7.0), "pH": (3.0, 4.5), "Acid": (0.05, 0.20)},
    "에너지음료": {"Brix": (10.0, 14.0), "pH": (2.5, 4.0), "Acid": (0.10, 0.30)},
    "식물성음료": {"Brix": (3.0, 10.0), "pH": (6.0, 7.5), "Acid": (0.00, 0.10)},
    "기능성음료": {"Brix": (4.0, 12.0), "pH": (2.8, 4.5), "Acid": (0.05, 0.30)},
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
        "Brix": "Brix",
        "브릭스": "Brix",
        "pH": "pH",
        "산도(%)": "Acidity",
        "Acidity": "Acidity",
        "산도": "Acidity",
        "감미도": "Sweetness",
        "Sweetness": "Sweetness",
        "Sweetness_Index": "Sweetness",
        "예상단가(원/kg)": "Cost",
        "단가": "Cost",
        "Cost_per_kg": "Cost",
        "Cost": "Cost",
        "Brix기여도(1%)": "Brix_Contribution",
        "Brix_Contribution": "Brix_Contribution",
        "산도기여도(1%)": "Acid_Contribution",
        "Acid_Contribution": "Acid_Contribution",
        "pH영향도(1%)": "pH_Effect",
        "pH_Effect": "pH_Effect",
        "FlavorContribution": "FlavorContribution",
        "Purpose": "Purpose",
        "pKa1": "pKa1",
        "pKa2": "pKa2",
        "Buffer_Capacity(β)": "Buffer_Capacity",
        "Buffer_Capacity": "Buffer_Capacity",
        "β": "Buffer_Capacity",
        "pH_Model_Type": "pH_Model_Type",
        "Ingredient_ID": "Ingredient_ID",
        "Flavor_ID": "Flavor_ID",
        "Ingredient_Role": "Ingredient_Role",
        "Role": "Ingredient_Role",
        "Typical_Range_Min_%": "Typical_Range_Min",
        "Typical_Range_Max_%": "Typical_Range_Max",
        "Typical_Range_Min": "Typical_Range_Min",
        "Typical_Range_Max": "Typical_Range_Max",
        "Beverage_Type": "Beverage_Type",
        "Function": "Function",
        "Color": "Color",
        "Origin": "Origin",
        "Supplier": "Supplier",
        "Solubility": "Solubility",
    }
    df = df.rename(columns=rename_map)
    return df


def enforce_numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    df = df.copy()
    for col in cols:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


def robust_json_extract(text: str) -> Optional[dict]:
    if not text or not isinstance(text, str):
        return None

    # 1) 직접 파싱 시도
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) ```json ... ``` 추출
    code_block = re.search(r"```json\s*(\{.*?\}|\[.*?\])\s*```", text, re.S)
    if code_block:
        try:
            return json.loads(code_block.group(1))
        except Exception:
            pass

    # 3) 객체 추출
    obj_match = re.search(r"(\{.*\})", text, re.S)
    if obj_match:
        try:
            return json.loads(obj_match.group(1))
        except Exception:
            pass

    # 4) 배열 추출
    arr_match = re.search(r"(\[.*\])", text, re.S)
    if arr_match:
        try:
            return {"items": json.loads(arr_match.group(1))}
        except Exception:
            pass

    return None


def get_openai_client(api_key: str):
    if not api_key:
        return None, "API key 미입력"
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        return client, None
    except Exception as e:
        return None, f"OpenAI 클라이언트 생성 실패: {e}"


# =========================================================
# 샘플 / fallback 데이터 생성
# =========================================================
def build_sample_ingredient_master() -> pd.DataFrame:
    rows = [
        # Water / Base
        {"Ingredient_ID": 1, "Ingredient_Name": "정제수", "Category": "Water", "Sub_Category": "Base", "Origin": "국내", "Supplier": "Sample", "Cost": 5, "Solubility": "High", "Color": "Clear"},
        # Sugars
        {"Ingredient_ID": 2, "Ingredient_Name": "설탕", "Category": "Sugar", "Sub_Category": "Sucrose", "Origin": "수입", "Supplier": "Sample", "Cost": 1200, "Solubility": "High", "Color": "White"},
        {"Ingredient_ID": 3, "Ingredient_Name": "액상과당", "Category": "Sugar", "Sub_Category": "HFCS", "Origin": "국내", "Supplier": "Sample", "Cost": 900, "Solubility": "High", "Color": "Clear"},
        # Sweeteners
        {"Ingredient_ID": 4, "Ingredient_Name": "수크랄로스", "Category": "Sweetener", "Sub_Category": "HighIntensity", "Origin": "수입", "Supplier": "Sample", "Cost": 150000, "Solubility": "High", "Color": "White"},
        {"Ingredient_ID": 5, "Ingredient_Name": "아세설팜K", "Category": "Sweetener", "Sub_Category": "HighIntensity", "Origin": "수입", "Supplier": "Sample", "Cost": 98000, "Solubility": "High", "Color": "White"},
        # Acids
        {"Ingredient_ID": 6, "Ingredient_Name": "구연산", "Category": "Acid", "Sub_Category": "Citric", "Origin": "수입", "Supplier": "Sample", "Cost": 3500, "Solubility": "High", "Color": "White"},
        {"Ingredient_ID": 7, "Ingredient_Name": "사과산", "Category": "Acid", "Sub_Category": "Malic", "Origin": "수입", "Supplier": "Sample", "Cost": 4200, "Solubility": "High", "Color": "White"},
        {"Ingredient_ID": 8, "Ingredient_Name": "인산", "Category": "Acid", "Sub_Category": "Phosphoric", "Origin": "수입", "Supplier": "Sample", "Cost": 2800, "Solubility": "High", "Color": "Clear"},
        # Extract
        {"Ingredient_ID": 9, "Ingredient_Name": "녹차추출물", "Category": "Extract", "Sub_Category": "Tea", "Origin": "국내", "Supplier": "Sample", "Cost": 45000, "Solubility": "Medium", "Color": "Brown"},
        {"Ingredient_ID": 10, "Ingredient_Name": "생강추출물", "Category": "Extract", "Sub_Category": "Spice", "Origin": "국내", "Supplier": "Sample", "Cost": 38000, "Solubility": "Medium", "Color": "Yellow"},
        {"Ingredient_ID": 11, "Ingredient_Name": "히비스커스추출물", "Category": "Extract", "Sub_Category": "Botanical", "Origin": "수입", "Supplier": "Sample", "Cost": 41000, "Solubility": "Medium", "Color": "Red"},
        # Concentrates
        {"Ingredient_ID": 12, "Ingredient_Name": "레몬농축액", "Category": "Concentrate", "Sub_Category": "Citrus", "Origin": "수입", "Supplier": "Sample", "Cost": 8000, "Solubility": "High", "Color": "Yellow"},
        {"Ingredient_ID": 13, "Ingredient_Name": "오렌지농축액", "Category": "Concentrate", "Sub_Category": "Citrus", "Origin": "수입", "Supplier": "Sample", "Cost": 7000, "Solubility": "High", "Color": "Orange"},
        {"Ingredient_ID": 14, "Ingredient_Name": "사과농축액", "Category": "Concentrate", "Sub_Category": "Fruit", "Origin": "수입", "Supplier": "Sample", "Cost": 6500, "Solubility": "High", "Color": "Amber"},
        {"Ingredient_ID": 15, "Ingredient_Name": "망고농축액", "Category": "Concentrate", "Sub_Category": "Tropical", "Origin": "수입", "Supplier": "Sample", "Cost": 8200, "Solubility": "High", "Color": "Orange"},
        {"Ingredient_ID": 16, "Ingredient_Name": "복숭아농축액", "Category": "Concentrate", "Sub_Category": "StoneFruit", "Origin": "수입", "Supplier": "Sample", "Cost": 7800, "Solubility": "High", "Color": "Orange"},
        {"Ingredient_ID": 17, "Ingredient_Name": "포도농축액", "Category": "Concentrate", "Sub_Category": "Berry", "Origin": "수입", "Supplier": "Sample", "Cost": 7200, "Solubility": "High", "Color": "Purple"},
        {"Ingredient_ID": 18, "Ingredient_Name": "파인애플농축액", "Category": "Concentrate", "Sub_Category": "Tropical", "Origin": "수입", "Supplier": "Sample", "Cost": 7500, "Solubility": "High", "Color": "Yellow"},
        # Stabilizer
        {"Ingredient_ID": 19, "Ingredient_Name": "펙틴", "Category": "Stabilizer", "Sub_Category": "Hydrocolloid", "Origin": "수입", "Supplier": "Sample", "Cost": 22000, "Solubility": "Medium", "Color": "White"},
        {"Ingredient_ID": 20, "Ingredient_Name": "잔탄검", "Category": "Stabilizer", "Sub_Category": "Hydrocolloid", "Origin": "수입", "Supplier": "Sample", "Cost": 18000, "Solubility": "Medium", "Color": "Cream"},
        # Color
        {"Ingredient_ID": 21, "Ingredient_Name": "카라멜색소", "Category": "Color", "Sub_Category": "Brown", "Origin": "국내", "Supplier": "Sample", "Cost": 6000, "Solubility": "High", "Color": "Brown"},
        {"Ingredient_ID": 22, "Ingredient_Name": "베타카로틴", "Category": "Color", "Sub_Category": "Orange", "Origin": "수입", "Supplier": "Sample", "Cost": 50000, "Solubility": "Low", "Color": "Orange"},
        {"Ingredient_ID": 23, "Ingredient_Name": "안토시아닌색소", "Category": "Color", "Sub_Category": "RedPurple", "Origin": "수입", "Supplier": "Sample", "Cost": 47000, "Solubility": "Medium", "Color": "Purple"},
        # Vitamins / Functional
        {"Ingredient_ID": 24, "Ingredient_Name": "비타민C", "Category": "Vitamin", "Sub_Category": "VitaminC", "Origin": "수입", "Supplier": "Sample", "Cost": 15000, "Solubility": "High", "Color": "White"},
        {"Ingredient_ID": 25, "Ingredient_Name": "비타민B군믹스", "Category": "Vitamin", "Sub_Category": "VitaminB", "Origin": "수입", "Supplier": "Sample", "Cost": 30000, "Solubility": "High", "Color": "Yellow"},
        {"Ingredient_ID": 26, "Ingredient_Name": "타우린", "Category": "Functional", "Sub_Category": "AminoAcid", "Origin": "수입", "Supplier": "Sample", "Cost": 18000, "Solubility": "High", "Color": "White"},
        {"Ingredient_ID": 27, "Ingredient_Name": "카페인", "Category": "Functional", "Sub_Category": "Stimulant", "Origin": "수입", "Supplier": "Sample", "Cost": 95000, "Solubility": "Medium", "Color": "White"},
        {"Ingredient_ID": 28, "Ingredient_Name": "L-카르니틴", "Category": "Functional", "Sub_Category": "Functional", "Origin": "수입", "Supplier": "Sample", "Cost": 65000, "Solubility": "High", "Color": "White"},
        {"Ingredient_ID": 29, "Ingredient_Name": "염화나트륨", "Category": "Electrolyte", "Sub_Category": "Na", "Origin": "국내", "Supplier": "Sample", "Cost": 800, "Solubility": "High", "Color": "White"},
        {"Ingredient_ID": 30, "Ingredient_Name": "염화칼륨", "Category": "Electrolyte", "Sub_Category": "K", "Origin": "수입", "Supplier": "Sample", "Cost": 2500, "Solubility": "High", "Color": "White"},
    ]
    return pd.DataFrame(rows)


def build_sample_ingredient_property() -> pd.DataFrame:
    rows = [
        {"Ingredient_ID": 1, "Brix": 0.0, "pH": 7.0, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0, "pKa1": 0.0, "pKa2": 0.0, "Buffer_Capacity": 0.0, "pH_Model_Type": "neutral"},
        {"Ingredient_ID": 2, "Brix": 100.0, "pH": 7.0, "Acidity": 0.0, "Sweetness": 1.0, "Brix_Contribution": 1.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0, "pKa1": 0.0, "pKa2": 0.0, "Buffer_Capacity": 0.0, "pH_Model_Type": "neutral"},
        {"Ingredient_ID": 3, "Brix": 77.0, "pH": 6.5, "Acidity": 0.0, "Sweetness": 1.1, "Brix_Contribution": 0.77, "Acid_Contribution": 0.0, "pH_Effect": 0.0, "pKa1": 0.0, "pKa2": 0.0, "Buffer_Capacity": 0.0, "pH_Model_Type": "neutral"},
        {"Ingredient_ID": 4, "Brix": 0.0, "pH": 6.0, "Acidity": 0.0, "Sweetness": 600.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0, "pKa1": 0.0, "pKa2": 0.0, "Buffer_Capacity": 0.0, "pH_Model_Type": "neutral"},
        {"Ingredient_ID": 5, "Brix": 0.0, "pH": 6.0, "Acidity": 0.0, "Sweetness": 200.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0, "pKa1": 0.0, "pKa2": 0.0, "Buffer_Capacity": 0.0, "pH_Model_Type": "neutral"},
        {"Ingredient_ID": 6, "Brix": 0.0, "pH": 2.2, "Acidity": 100.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 1.0, "pH_Effect": -0.30, "pKa1": 3.13, "pKa2": 4.76, "Buffer_Capacity": 0.40, "pH_Model_Type": "buffered"},
        {"Ingredient_ID": 7, "Brix": 0.0, "pH": 2.6, "Acidity": 100.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 1.0, "pH_Effect": -0.25, "pKa1": 3.40, "pKa2": 5.11, "Buffer_Capacity": 0.35, "pH_Model_Type": "buffered"},
        {"Ingredient_ID": 8, "Brix": 0.0, "pH": 1.8, "Acidity": 85.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.85, "pH_Effect": -0.35, "pKa1": 2.15, "pKa2": 7.20, "Buffer_Capacity": 0.45, "pH_Model_Type": "buffered"},
        {"Ingredient_ID": 9, "Brix": 2.0, "pH": 5.8, "Acidity": 0.2, "Sweetness": 0.1, "Brix_Contribution": 0.02, "Acid_Contribution": 0.002, "pH_Effect": -0.002, "pKa1": 0.0, "pKa2": 0.0, "Buffer_Capacity": 0.05, "pH_Model_Type": "linear"},
        {"Ingredient_ID": 10, "Brix": 4.0, "pH": 5.2, "Acidity": 0.3, "Sweetness": 0.1, "Brix_Contribution": 0.04, "Acid_Contribution": 0.003, "pH_Effect": -0.003, "pKa1": 0.0, "pKa2": 0.0, "Buffer_Capacity": 0.06, "pH_Model_Type": "linear"},
        {"Ingredient_ID": 11, "Brix": 3.0, "pH": 3.1, "Acidity": 0.8, "Sweetness": 0.2, "Brix_Contribution": 0.03, "Acid_Contribution": 0.008, "pH_Effect": -0.010, "pKa1": 0.0, "pKa2": 0.0, "Buffer_Capacity": 0.07, "pH_Model_Type": "linear"},
        {"Ingredient_ID": 12, "Brix": 65.0, "pH": 2.2, "Acidity": 6.5, "Sweetness": 0.8, "Brix_Contribution": 0.65, "Acid_Contribution": 0.065, "pH_Effect": -0.060, "pKa1": 3.13, "pKa2": 4.76, "Buffer_Capacity": 0.35, "pH_Model_Type": "buffered"},
        {"Ingredient_ID": 13, "Brix": 65.0, "pH": 3.2, "Acidity": 1.2, "Sweetness": 0.9, "Brix_Contribution": 0.65, "Acid_Contribution": 0.012, "pH_Effect": -0.012, "pKa1": 3.40, "pKa2": 4.76, "Buffer_Capacity": 0.18, "pH_Model_Type": "buffered"},
        {"Ingredient_ID": 14, "Brix": 70.0, "pH": 3.5, "Acidity": 0.8, "Sweetness": 0.9, "Brix_Contribution": 0.70, "Acid_Contribution": 0.008, "pH_Effect": -0.008, "pKa1": 3.40, "pKa2": 5.11, "Buffer_Capacity": 0.15, "pH_Model_Type": "buffered"},
        {"Ingredient_ID": 15, "Brix": 65.0, "pH": 3.6, "Acidity": 0.9, "Sweetness": 1.0, "Brix_Contribution": 0.65, "Acid_Contribution": 0.009, "pH_Effect": -0.009, "pKa1": 3.40, "pKa2": 5.11, "Buffer_Capacity": 0.16, "pH_Model_Type": "buffered"},
        {"Ingredient_ID": 16, "Brix": 66.0, "pH": 3.5, "Acidity": 0.7, "Sweetness": 0.9, "Brix_Contribution": 0.66, "Acid_Contribution": 0.007, "pH_Effect": -0.007, "pKa1": 3.40, "pKa2": 5.11, "Buffer_Capacity": 0.14, "pH_Model_Type": "buffered"},
        {"Ingredient_ID": 17, "Brix": 68.0, "pH": 3.4, "Acidity": 0.7, "Sweetness": 0.8, "Brix_Contribution": 0.68, "Acid_Contribution": 0.007, "pH_Effect": -0.007, "pKa1": 3.40, "pKa2": 5.11, "Buffer_Capacity": 0.14, "pH_Model_Type": "buffered"},
        {"Ingredient_ID": 18, "Brix": 60.0, "pH": 3.3, "Acidity": 1.5, "Sweetness": 0.9, "Brix_Contribution": 0.60, "Acid_Contribution": 0.015, "pH_Effect": -0.015, "pKa1": 3.40, "pKa2": 5.11, "Buffer_Capacity": 0.18, "pH_Model_Type": "buffered"},
        {"Ingredient_ID": 19, "Brix": 0.0, "pH": 4.0, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0, "pKa1": 0.0, "pKa2": 0.0, "Buffer_Capacity": 0.05, "pH_Model_Type": "linear"},
        {"Ingredient_ID": 20, "Brix": 0.0, "pH": 6.0, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0, "pKa1": 0.0, "pKa2": 0.0, "Buffer_Capacity": 0.05, "pH_Model_Type": "linear"},
        {"Ingredient_ID": 21, "Brix": 0.0, "pH": 4.0, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0, "pKa1": 0.0, "pKa2": 0.0, "Buffer_Capacity": 0.0, "pH_Model_Type": "neutral"},
        {"Ingredient_ID": 22, "Brix": 0.0, "pH": 6.0, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0, "pKa1": 0.0, "pKa2": 0.0, "Buffer_Capacity": 0.0, "pH_Model_Type": "neutral"},
        {"Ingredient_ID": 23, "Brix": 0.0, "pH": 4.0, "Acidity": 0.1, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.001, "pH_Effect": -0.001, "pKa1": 0.0, "pKa2": 0.0, "Buffer_Capacity": 0.0, "pH_Model_Type": "neutral"},
        {"Ingredient_ID": 24, "Brix": 0.0, "pH": 2.4, "Acidity": 100.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 1.0, "pH_Effect": -0.26, "pKa1": 4.10, "pKa2": 11.60, "Buffer_Capacity": 0.25, "pH_Model_Type": "buffered"},
        {"Ingredient_ID": 25, "Brix": 0.0, "pH": 5.0, "Acidity": 0.2, "Sweetness": 0.1, "Brix_Contribution": 0.0, "Acid_Contribution": 0.002, "pH_Effect": -0.002, "pKa1": 0.0, "pKa2": 0.0, "Buffer_Capacity": 0.05, "pH_Model_Type": "linear"},
        {"Ingredient_ID": 26, "Brix": 0.0, "pH": 6.0, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0, "pKa1": 0.0, "pKa2": 0.0, "Buffer_Capacity": 0.05, "pH_Model_Type": "neutral"},
        {"Ingredient_ID": 27, "Brix": 0.0, "pH": 6.5, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0, "pKa1": 14.0, "pKa2": 0.0, "Buffer_Capacity": 0.01, "pH_Model_Type": "neutral"},
        {"Ingredient_ID": 28, "Brix": 0.0, "pH": 6.5, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0, "pKa1": 0.0, "pKa2": 0.0, "Buffer_Capacity": 0.02, "pH_Model_Type": "neutral"},
        {"Ingredient_ID": 29, "Brix": 0.0, "pH": 7.0, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0, "pKa1": 0.0, "pKa2": 0.0, "Buffer_Capacity": 0.01, "pH_Model_Type": "neutral"},
        {"Ingredient_ID": 30, "Brix": 0.0, "pH": 7.0, "Acidity": 0.0, "Sweetness": 0.0, "Brix_Contribution": 0.0, "Acid_Contribution": 0.0, "pH_Effect": 0.0, "pKa1": 0.0, "pKa2": 0.0, "Buffer_Capacity": 0.01, "pH_Model_Type": "neutral"},
    ]
    return pd.DataFrame(rows)


def build_sample_flavor_master() -> pd.DataFrame:
    rows = []
    flavor_id = 1
    for bev_type, flavors in TREND_FLAVORS.items():
        for f in flavors:
            rows.append({
                "Flavor_ID": flavor_id,
                "Flavor": f,
                "Beverage_Type": bev_type,
                "Trend_Score": random.randint(60, 95),
                "Market_Region": "KR/Global",
            })
            flavor_id += 1
    return pd.DataFrame(rows)


def build_sample_flavor_map(master_df: pd.DataFrame) -> pd.DataFrame:
    flavor_rows = []
    for _, row in master_df.iterrows():
        flavor = row["Flavor"]
        bev_type = row["Beverage_Type"]
        flavor_l = flavor.lower()

        default_items = [
            ("정제수", "Water", 70.0, 95.0, "Base"),
            ("설탕", "Sugar", 0.0, 12.0, "Sweetness"),
            ("수크랄로스", "Sweetener", 0.0, 0.03, "Sweetness"),
            ("구연산", "Acid", 0.05, 0.30, "Acidity"),
            ("펙틴", "Stabilizer", 0.0, 0.20, "Stability"),
        ]

        if bev_type == "탄산음료":
            default_items += [("카라멜색소", "Color", 0.0, 0.01, "Color")]
        if bev_type == "스포츠음료":
            default_items += [("염화나트륨", "Electrolyte", 0.05, 0.20, "Electrolyte"),
                              ("염화칼륨", "Electrolyte", 0.01, 0.10, "Electrolyte")]
        if bev_type == "에너지음료":
            default_items += [("타우린", "Functional", 0.20, 0.40, "Energy"),
                              ("카페인", "Functional", 0.01, 0.04, "Energy"),
                              ("비타민B군믹스", "Vitamin", 0.01, 0.05, "Vitamin")]
        if bev_type == "기능성음료":
            default_items += [("비타민C", "Vitamin", 0.02, 0.10, "Function")]
        if bev_type == "식물성음료":
            default_items += [("잔탄검", "Stabilizer", 0.05, 0.20, "Mouthfeel")]

        # flavor keyword 기반 집중 재료
        keyword_items = []
        if any(k in flavor_l for k in ["lemon", "lime", "yuzu", "citrus"]):
            keyword_items += [("레몬농축액", "Concentrate", 0.5, 12.0, "Flavor")]
        if "orange" in flavor_l or "grapefruit" in flavor_l:
            keyword_items += [("오렌지농축액", "Concentrate", 0.5, 15.0, "Flavor")]
        if any(k in flavor_l for k in ["apple"]):
            keyword_items += [("사과농축액", "Concentrate", 0.5, 15.0, "Flavor")]
        if any(k in flavor_l for k in ["mango", "tropical"]):
            keyword_items += [("망고농축액", "Concentrate", 0.5, 18.0, "Flavor")]
        if any(k in flavor_l for k in ["peach"]):
            keyword_items += [("복숭아농축액", "Concentrate", 0.5, 15.0, "Flavor")]
        if any(k in flavor_l for k in ["berry", "grape", "hibiscus"]):
            keyword_items += [("포도농축액", "Concentrate", 0.5, 15.0, "Flavor"),
                              ("히비스커스추출물", "Extract", 0.02, 0.30, "Flavor")]
        if any(k in flavor_l for k in ["pineapple"]):
            keyword_items += [("파인애플농축액", "Concentrate", 0.5, 15.0, "Flavor")]
        if any(k in flavor_l for k in ["ginger"]):
            keyword_items += [("생강추출물", "Extract", 0.01, 0.20, "Flavor")]
        if any(k in flavor_l for k in ["matcha"]):
            keyword_items += [("녹차추출물", "Extract", 0.05, 0.30, "Flavor")]

        all_items = default_items + keyword_items

        for ing_name, role, min_v, max_v, func in all_items:
            flavor_rows.append({
                "Flavor_ID": row["Flavor_ID"],
                "Flavor": flavor,
                "Beverage_Type": bev_type,
                "Ingredient_Name": ing_name,
                "Ingredient_Role": role,
                "Typical_Range_Min": min_v,
                "Typical_Range_Max": max_v,
                "Function": func,
            })
    return pd.DataFrame(flavor_rows)


def build_sample_beverage_template() -> pd.DataFrame:
    rows = []
    for bev_type, role_dict in TYPE_TEMPLATES.items():
        for role, (low, high) in role_dict.items():
            rows.append({
                "Beverage_Type": bev_type,
                "Ingredient_Role": role,
                "Typical_Range_Min": low,
                "Typical_Range_Max": high,
            })
    return pd.DataFrame(rows)


def expand_to_500_ingredients(master_df: pd.DataFrame, prop_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    API 미사용 fallback: 기본 원료를 규칙 기반으로 확장해 500종 수준까지 생성
    """
    random.seed(42)
    np.random.seed(42)

    base_master = master_df.copy()
    base_prop = prop_df.copy()

    categories = [
        ("Sugar", 80),
        ("Acid", 50),
        ("Extract", 120),
        ("Concentrate", 80),
        ("Sweetener", 40),
        ("Stabilizer", 40),
        ("Color", 30),
        ("Vitamin", 30),
        ("Functional", 30),
    ]

    existing_ids = set(base_master["Ingredient_ID"].tolist())
    next_id = max(existing_ids) + 1 if existing_ids else 1

    generated_master = []
    generated_prop = []

    for category, target_count in categories:
        existing_cat = base_master[base_master["Category"] == category]
        need = max(0, target_count - len(existing_cat))

        if existing_cat.empty:
            # 정말 비었을 때 최소 seed
            seed_name = f"{category}_Base"
            existing_cat = pd.DataFrame([{
                "Ingredient_ID": -1,
                "Ingredient_Name": seed_name,
                "Category": category,
                "Sub_Category": "Base",
                "Origin": "Sample",
                "Supplier": "Sample",
                "Cost": 1000,
                "Solubility": "High",
                "Color": "Clear",
            }])

        existing_ids_cat = existing_cat["Ingredient_ID"].tolist()

        prop_seed = base_prop[base_prop["Ingredient_ID"].isin(existing_ids_cat)]
        if prop_seed.empty:
            prop_seed = pd.DataFrame([{
                "Ingredient_ID": existing_ids_cat[0],
                "Brix": 0.0,
                "pH": 7.0,
                "Acidity": 0.0,
                "Sweetness": 0.0,
                "Brix_Contribution": 0.0,
                "Acid_Contribution": 0.0,
                "pH_Effect": 0.0,
                "pKa1": 0.0,
                "pKa2": 0.0,
                "Buffer_Capacity": 0.05,
                "pH_Model_Type": "linear",
            }])

        for i in range(need):
            seed_master = existing_cat.iloc[i % len(existing_cat)].to_dict()
            seed_prop_row = prop_seed.iloc[i % len(prop_seed)].to_dict()

            new_name = f"{seed_master['Ingredient_Name']}_{i+1:03d}"
            new_cost = round(safe_float(seed_master.get("Cost"), 1000) * random.uniform(0.85, 1.20), 2)

            generated_master.append({
                "Ingredient_ID": next_id,
                "Ingredient_Name": new_name,
                "Category": seed_master.get("Category", category),
                "Sub_Category": seed_master.get("Sub_Category", "Variant"),
                "Origin": seed_master.get("Origin", "Sample"),
                "Supplier": seed_master.get("Supplier", "Sample"),
                "Cost": new_cost,
                "Solubility": seed_master.get("Solubility", "High"),
                "Color": seed_master.get("Color", "Clear"),
            })

            brix = clamp(safe_float(seed_prop_row.get("Brix"), 0.0) * random.uniform(0.9, 1.1), 0, 1000)
            ph = clamp(safe_float(seed_prop_row.get("pH"), 7.0) * random.uniform(0.95, 1.05), 0.5, 14.0)
            acidity = clamp(safe_float(seed_prop_row.get("Acidity"), 0.0) * random.uniform(0.9, 1.1), 0, 100)
            sweetness = clamp(safe_float(seed_prop_row.get("Sweetness"), 0.0) * random.uniform(0.9, 1.1), 0, 1000)
            brix_c = clamp(safe_float(seed_prop_row.get("Brix_Contribution"), 0.0) * random.uniform(0.9, 1.1), 0, 10)
            acid_c = clamp(safe_float(seed_prop_row.get("Acid_Contribution"), 0.0) * random.uniform(0.9, 1.1), 0, 10)
            ph_effect = safe_float(seed_prop_row.get("pH_Effect"), 0.0) * random.uniform(0.9, 1.1)

            generated_prop.append({
                "Ingredient_ID": next_id,
                "Brix": round(brix, 4),
                "pH": round(ph, 4),
                "Acidity": round(acidity, 4),
                "Sweetness": round(sweetness, 4),
                "Brix_Contribution": round(brix_c, 4),
                "Acid_Contribution": round(acid_c, 4),
                "pH_Effect": round(ph_effect, 4),
                "pKa1": safe_float(seed_prop_row.get("pKa1"), 0.0),
                "pKa2": safe_float(seed_prop_row.get("pKa2"), 0.0),
                "Buffer_Capacity": max(0.0, round(safe_float(seed_prop_row.get("Buffer_Capacity"), 0.05) * random.uniform(0.9, 1.1), 4)),
                "pH_Model_Type": seed_prop_row.get("pH_Model_Type", "linear"),
            })

            next_id += 1

    full_master = pd.concat([base_master, pd.DataFrame(generated_master)], ignore_index=True)
    full_prop = pd.concat([base_prop, pd.DataFrame(generated_prop)], ignore_index=True)

    full_master = full_master.drop_duplicates(subset=["Ingredient_ID"]).reset_index(drop=True)
    full_prop = full_prop.drop_duplicates(subset=["Ingredient_ID"]).reset_index(drop=True)

    return full_master, full_prop


# =========================================================
# 엑셀 로드 / fallback
# =========================================================
@st.cache_data(show_spinner=False)
def load_or_build_db(excel_path: str) -> Dict[str, pd.DataFrame]:
    result: Dict[str, pd.DataFrame] = {}

    def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
        return normalize_columns(df)

    if excel_path and os.path.exists(excel_path):
        try:
            xls = pd.ExcelFile(excel_path)
            for sheet in xls.sheet_names:
                try:
                    df = pd.read_excel(xls, sheet_name=sheet)
                    result[sheet] = normalize_df(df)
                except Exception:
                    continue
        except Exception:
            result = {}

    # 내부 표준 키로 변환
    master = None
    prop = None
    flavor_master = None
    flavor_map = None
    beverage_template = None

    for name, df in result.items():
        cols = set(df.columns)
        if {"Ingredient_ID", "Ingredient_Name", "Category"}.issubset(cols):
            master = df.copy()
        elif {"Ingredient_ID", "Brix", "pH"}.issubset(cols):
            prop = df.copy()
        elif {"Flavor_ID", "Flavor", "Beverage_Type"}.issubset(cols) and "Trend_Score" in cols:
            flavor_master = df.copy()
        elif {"Flavor_ID", "Ingredient_Name", "Ingredient_Role"}.issubset(cols):
            flavor_map = df.copy()
        elif {"Beverage_Type", "Ingredient_Role", "Typical_Range_Min", "Typical_Range_Max"}.issubset(cols):
            beverage_template = df.copy()

    # fallback 생성
    if master is None:
        master = normalize_columns(build_sample_ingredient_master())
    if prop is None:
        prop = normalize_columns(build_sample_ingredient_property())
    if flavor_master is None:
        flavor_master = normalize_columns(build_sample_flavor_master())
    if flavor_map is None:
        flavor_map = normalize_columns(build_sample_flavor_map(flavor_master))
    if beverage_template is None:
        beverage_template = normalize_columns(build_sample_beverage_template())

    master = enforce_numeric(master, ["Ingredient_ID", "Cost"])
    prop = enforce_numeric(prop, ["Ingredient_ID", "Brix", "pH", "Acidity", "Sweetness",
                                  "Brix_Contribution", "Acid_Contribution", "pH_Effect",
                                  "pKa1", "pKa2", "Buffer_Capacity"])
    flavor_master = enforce_numeric(flavor_master, ["Flavor_ID", "Trend_Score"])
    flavor_map = enforce_numeric(flavor_map, ["Flavor_ID", "Typical_Range_Min", "Typical_Range_Max"])
    beverage_template = enforce_numeric(beverage_template, ["Typical_Range_Min", "Typical_Range_Max"])

    return {
        "Ingredient_Master": master,
        "Ingredient_Property": prop,
        "Flavor_Master": flavor_master,
        "Flavor_Ingredient_Map": flavor_map,
        "Beverage_Type_Template": beverage_template,
    }


def merge_ingredient_data(master_df: pd.DataFrame, prop_df: pd.DataFrame) -> pd.DataFrame:
    df = pd.merge(master_df, prop_df, on="Ingredient_ID", how="left")
    df = normalize_columns(df)
    df = enforce_numeric(df, ["Brix", "pH", "Acidity", "Sweetness", "Cost",
                              "Brix_Contribution", "Acid_Contribution", "pH_Effect",
                              "pKa1", "pKa2", "Buffer_Capacity"])
    for col in ["Ingredient_Name", "Category", "Sub_Category", "Origin", "Supplier", "Solubility", "Color"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)
    return df


# =========================================================
# OpenAI 보조 함수
# =========================================================
def generate_trend_products_with_api(client, model_name: str, beverage_type: str) -> Optional[List[str]]:
    prompt = f"""
You are a beverage trend strategist.
Generate exactly 20 beverage flavor product names for beverage type: {beverage_type}.
Return strict JSON only in this format:
{{
  "items": ["name1", "name2", ..., "name20"]
}}
No explanation.
""".strip()

    try:
        resp = client.chat.completions.create(
            model=model_name,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You output strict JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        content = resp.choices[0].message.content or ""
        parsed = robust_json_extract(content)
        if parsed and isinstance(parsed, dict) and "items" in parsed and isinstance(parsed["items"], list):
            items = [str(x).strip() for x in parsed["items"] if str(x).strip()]
            if len(items) >= 20:
                return items[:20]
    except Exception:
        return None
    return None


def generate_ingredient_db_with_api(client, model_name: str, beverage_type: str, flavor_name: str) -> Optional[pd.DataFrame]:
    prompt = f"""
Generate ingredient database candidates for a beverage formulation.
Beverage type: {beverage_type}
Flavor: {flavor_name}

Return strict JSON object only:
{{
  "items": [
    {{
      "Ingredient_Name": "...",
      "Category": "...",
      "Sub_Category": "...",
      "Flavor": "{flavor_name}",
      "Brix": 0,
      "pH": 7,
      "Acidity": 0,
      "Sweetness": 0,
      "Cost": 0,
      "Purpose": "...",
      "FlavorContribution": 0.0,
      "Brix_Contribution": 0.0,
      "Acid_Contribution": 0.0,
      "pH_Effect": 0.0,
      "pKa1": 0.0,
      "pKa2": 0.0,
      "Buffer_Capacity": 0.0,
      "pH_Model_Type": "linear"
    }}
  ]
}}

Need around 120 diverse ingredients relevant to the beverage type and flavor.
No explanations.
""".strip()

    try:
        resp = client.chat.completions.create(
            model=model_name,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You output strict JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
        )
        content = resp.choices[0].message.content or ""
        parsed = robust_json_extract(content)
        if parsed and isinstance(parsed, dict) and "items" in parsed and isinstance(parsed["items"], list):
            df = pd.DataFrame(parsed["items"])
            if not df.empty:
                return normalize_columns(df)
    except Exception:
        return None
    return None


def ai_rd_evaluation_with_api(client, model_name: str, beverage_type: str, flavor_name: str, formula_table: pd.DataFrame, summary: FormulaSummary) -> Optional[str]:
    preview = formula_table[["Ingredient_Name", "Ingredient_Role", "Usage_%", "Cost_Contribution", "Brix_Contribution_Value", "Acid_Contribution_Value", "Sweetness_Contribution_Value"]].to_dict(orient="records")
    prompt = f"""
You are a beverage R&D scientist.
Evaluate this beverage formulation in Korean.

Beverage type: {beverage_type}
Flavor: {flavor_name}

Formula summary:
- Brix: {summary.total_brix}
- pH: {summary.total_ph}
- Acid: {summary.total_acid}
- Sweetness: {summary.total_sweetness}
- Cost: {summary.total_cost}
- Score: {summary.score}

Formula rows:
{json.dumps(preview, ensure_ascii=False)}

Please provide:
1. 풍미 밸런스 평가
2. 감미 밸런스 평가
3. 산미 밸런스 평가
4. 바디감/마우스필 평가
5. 기술적 개선 제안
""".strip()

    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a senior beverage R&D scientist. Respond in Korean."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
        )
        content = resp.choices[0].message.content or ""
        return content.strip() if content else None
    except Exception:
        return None


# =========================================================
# Flavor / 원료 필터링
# =========================================================
def generate_trend_products(beverage_type: str, api_client=None, model_name: str = "gpt-5.4") -> List[str]:
    if api_client is not None:
        api_items = generate_trend_products_with_api(api_client, model_name, beverage_type)
        if api_items:
            return api_items
    return TREND_FLAVORS.get(beverage_type, [])[:20]


def build_flavor_mapping_fallback(flavor_name: str, beverage_type: str, ingredient_df: pd.DataFrame) -> pd.DataFrame:
    flavor_master = pd.DataFrame([{
        "Flavor_ID": 999999,
        "Flavor": flavor_name,
        "Beverage_Type": beverage_type,
        "Trend_Score": 80,
        "Market_Region": "Fallback",
    }])
    return build_sample_flavor_map(flavor_master)


def filter_ingredient_by_flavor(
    ingredient_df: pd.DataFrame,
    flavor_map_df: pd.DataFrame,
    flavor_name: str,
    beverage_type: str,
) -> pd.DataFrame:
    ingredient_df = ingredient_df.copy()
    flavor_map_df = flavor_map_df.copy()

    for col in ["Flavor", "Beverage_Type", "Ingredient_Name", "Ingredient_Role"]:
        if col not in flavor_map_df.columns:
            flavor_map_df[col] = ""

    matched = flavor_map_df[
        (flavor_map_df["Flavor"].astype(str).str.lower() == flavor_name.lower()) &
        (flavor_map_df["Beverage_Type"].astype(str) == beverage_type)
    ].copy()

    if matched.empty:
        matched = build_flavor_mapping_fallback(flavor_name, beverage_type, ingredient_df)

    df = ingredient_df.merge(
        matched[["Ingredient_Name", "Ingredient_Role", "Typical_Range_Min", "Typical_Range_Max", "Function"]],
        on="Ingredient_Name",
        how="inner",
    )

    if df.empty:
        # 최소 fallback
        essential_roles = TYPE_TEMPLATES.get(beverage_type, {})
        temp_rows = []
        for role in essential_roles.keys():
            cand = ingredient_df[ingredient_df["Category"].isin(role_to_categories(role))].copy()
            if not cand.empty:
                row = cand.iloc[0].to_dict()
                row["Ingredient_Role"] = role
                low, high = essential_roles[role]
                row["Typical_Range_Min"] = low
                row["Typical_Range_Max"] = high
                row["Function"] = role
                temp_rows.append(row)
        df = pd.DataFrame(temp_rows)

    if "FlavorContribution" not in df.columns:
        df["FlavorContribution"] = 0.0
    if "Purpose" not in df.columns:
        df["Purpose"] = df.get("Function", "")

    return df.reset_index(drop=True)


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


# =========================================================
# 표준배합 / 시뮬레이션 계산
# =========================================================
def get_type_template_df(beverage_type: str) -> pd.DataFrame:
    rows = []
    for role, (low, high) in TYPE_TEMPLATES.get(beverage_type, {}).items():
        rows.append({
            "Ingredient_Role": role,
            "Min_%": low,
            "Max_%": high,
            "Mid_%": round((low + high) / 2.0, 4),
        })
    return pd.DataFrame(rows)


def calculate_properties(formula_df: pd.DataFrame, beverage_type: str) -> FormulaSummary:
    """
    표준배합 템플릿과 AI 배합 결과가 반드시 같은 계산 함수를 쓰도록 고정.
    """
    if formula_df is None or formula_df.empty:
        return FormulaSummary(0.0, 0.0, 0.0, 0.0, 7.0, 999999.0)

    df = formula_df.copy()
    numeric_cols = [
        "Usage_%", "Brix", "Acidity", "Sweetness", "Cost",
        "Brix_Contribution", "Acid_Contribution", "pH_Effect",
        "pKa1", "pKa2", "Buffer_Capacity"
    ]
    df = enforce_numeric(df, numeric_cols)

    df["Brix_Contribution_Value"] = df["Usage_%"] * df["Brix"] / 100.0
    df["Acid_Contribution_Value"] = df["Usage_%"] * df["Acidity"] / 100.0
    df["Sweetness_Contribution_Value"] = df["Usage_%"] * df["Sweetness"] / 100.0
    df["Cost_Contribution"] = df["Usage_%"] * df["Cost"] / 100.0

    total_brix = round(df["Brix_Contribution_Value"].sum(), 4)
    total_acid = round(df["Acid_Contribution_Value"].sum(), 4)
    total_sweetness = round(df["Sweetness_Contribution_Value"].sum(), 4)
    total_cost = round(df["Cost_Contribution"].sum(), 4)

    # pH 계산: 고급 완충모델 우선 / 없으면 선형 fallback
    acid_rows = df[df["Ingredient_Role"].isin(["Acid", "Concentrate", "Extract"])].copy()
    buffer_beta = safe_float((acid_rows["Buffer_Capacity"] * acid_rows["Usage_%"]).sum(), 0.0)
    weighted_base_ph = 7.0

    if beverage_type in ["탄산음료", "과채음료", "에너지음료", "기능성음료", "스포츠음료"]:
        weighted_base_ph = 4.2
    elif beverage_type == "식물성음료":
        weighted_base_ph = 6.8

    has_buffer_model = (
        not acid_rows.empty and
        (acid_rows["pH_Model_Type"].astype(str).str.lower() == "buffered").any() and
        buffer_beta > 0
    )

    if has_buffer_model:
        total_ph = weighted_base_ph - (total_acid / max(buffer_beta, 0.05))
    else:
        linear_effect = safe_float((df["pH_Effect"] * df["Usage_%"]).sum(), 0.0)
        total_ph = weighted_base_ph + linear_effect

    total_ph = round(clamp(total_ph, 1.5, 8.0), 4)

    return FormulaSummary(
        total_brix=total_brix,
        total_acid=total_acid,
        total_sweetness=total_sweetness,
        total_cost=total_cost,
        total_ph=total_ph,
        score=0.0,
    )


def build_standard_formula_preview(filtered_df: pd.DataFrame, beverage_type: str) -> pd.DataFrame:
    """
    슬라이더 조정 전 참고용 표준배합 미리보기
    """
    template_df = get_type_template_df(beverage_type)
    rows = []

    for _, temp_row in template_df.iterrows():
        role = temp_row["Ingredient_Role"]
        role_candidates = filtered_df[filtered_df["Ingredient_Role"] == role].copy()

        if role_candidates.empty:
            role_candidates = filtered_df[filtered_df["Category"].isin(role_to_categories(role))].copy()

        if role_candidates.empty:
            continue

        chosen = role_candidates.iloc[0].to_dict()
        chosen["Usage_%"] = temp_row["Mid_%"]
        rows.append(chosen)

    if not rows:
        return pd.DataFrame()

    formula_df = pd.DataFrame(rows)
    formula_df = rebalance_water(formula_df, beverage_type)
    return formula_df


def rebalance_water(formula_df: pd.DataFrame, beverage_type: str) -> pd.DataFrame:
    df = formula_df.copy()
    if "Usage_%" not in df.columns:
        df["Usage_%"] = 0.0
    df["Usage_%"] = pd.to_numeric(df["Usage_%"], errors="coerce").fillna(0.0)

    non_water_sum = df.loc[df["Ingredient_Role"] != "Water", "Usage_%"].sum()
    water_value = round(max(0.0, 100.0 - non_water_sum), 4)

    water_idx = df.index[df["Ingredient_Role"] == "Water"].tolist()
    if water_idx:
        df.loc[water_idx[0], "Usage_%"] = water_value
    else:
        # Water row 없으면 추가
        water_row = {
            "Ingredient_ID": -999,
            "Ingredient_Name": "정제수",
            "Category": "Water",
            "Sub_Category": "Base",
            "Origin": "국내",
            "Supplier": "Auto",
            "Cost": 5.0,
            "Solubility": "High",
            "Color": "Clear",
            "Brix": 0.0,
            "pH": 7.0,
            "Acidity": 0.0,
            "Sweetness": 0.0,
            "Brix_Contribution": 0.0,
            "Acid_Contribution": 0.0,
            "pH_Effect": 0.0,
            "pKa1": 0.0,
            "pKa2": 0.0,
            "Buffer_Capacity": 0.0,
            "pH_Model_Type": "neutral",
            "FlavorContribution": 0.0,
            "Purpose": "Base",
            "Ingredient_Role": "Water",
            "Typical_Range_Min": TYPE_TEMPLATES.get(beverage_type, {}).get("Water", (70.0, 95.0))[0],
            "Typical_Range_Max": TYPE_TEMPLATES.get(beverage_type, {}).get("Water", (70.0, 95.0))[1],
            "Function": "Base",
            "Usage_%": water_value,
        }
        df = pd.concat([pd.DataFrame([water_row]), df], ignore_index=True)

    return df


# =========================================================
# 유전 알고리즘
# =========================================================
def create_individual(filtered_df: pd.DataFrame, beverage_type: str) -> pd.DataFrame:
    template = TYPE_TEMPLATES.get(beverage_type, {})
    rows = []

    for role, (low, high) in template.items():
        candidates = filtered_df[filtered_df["Ingredient_Role"] == role].copy()
        if candidates.empty:
            candidates = filtered_df[filtered_df["Category"].isin(role_to_categories(role))].copy()

        if candidates.empty and role != "Water":
            continue

        if role == "Water":
            water_row = {
                "Ingredient_ID": -999,
                "Ingredient_Name": "정제수",
                "Category": "Water",
                "Sub_Category": "Base",
                "Origin": "국내",
                "Supplier": "Auto",
                "Cost": 5.0,
                "Solubility": "High",
                "Color": "Clear",
                "Brix": 0.0,
                "pH": 7.0,
                "Acidity": 0.0,
                "Sweetness": 0.0,
                "Brix_Contribution": 0.0,
                "Acid_Contribution": 0.0,
                "pH_Effect": 0.0,
                "pKa1": 0.0,
                "pKa2": 0.0,
                "Buffer_Capacity": 0.0,
                "pH_Model_Type": "neutral",
                "FlavorContribution": 0.0,
                "Purpose": "Base",
                "Ingredient_Role": "Water",
                "Typical_Range_Min": low,
                "Typical_Range_Max": high,
                "Function": "Base",
                "Usage_%": 0.0,
            }
            rows.append(water_row)
            continue

        chosen = candidates.sample(1, random_state=random.randint(1, 100000)).iloc[0].to_dict()
        chosen["Usage_%"] = round(random.uniform(low, high), 4)
        rows.append(chosen)

    individual = pd.DataFrame(rows)
    individual = rebalance_water(individual, beverage_type)
    return individual


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
    if parent1.empty:
        return parent2.copy()
    if parent2.empty:
        return parent1.copy()

    roles = sorted(set(parent1["Ingredient_Role"].tolist()) | set(parent2["Ingredient_Role"].tolist()))
    rows = []
    for role in roles:
        source = parent1 if random.random() < 0.5 else parent2
        candidates = source[source["Ingredient_Role"] == role]
        if not candidates.empty:
            rows.append(candidates.iloc[0].to_dict())

    child = pd.DataFrame(rows)
    child = rebalance_water(child, beverage_type)
    return child


def mutate(formula_df: pd.DataFrame, beverage_type: str, mutation_rate: float = 0.20) -> pd.DataFrame:
    df = formula_df.copy()
    template = TYPE_TEMPLATES.get(beverage_type, {})

    if df.empty:
        return df

    for idx, row in df.iterrows():
        role = row.get("Ingredient_Role", "")
        if role == "Water":
            continue
        if random.random() < mutation_rate and role in template:
            low, high = template[role]
            df.at[idx, "Usage_%"] = round(random.uniform(low, high), 4)

    df = rebalance_water(df, beverage_type)
    return df


def optimize_formula(
    filtered_df: pd.DataFrame,
    beverage_type: str,
    target_brix: float,
    target_sweetness: float,
    target_acidity: float,
    population_size: int,
    generations: int,
) -> List[Tuple[pd.DataFrame, FormulaSummary]]:
    population = []
    for _ in range(max(10, population_size)):
        indiv = create_individual(filtered_df, beverage_type)
        score, summary = evaluate(indiv, beverage_type, target_brix, target_sweetness, target_acidity)
        population.append((indiv, summary))

    for _ in range(max(1, generations)):
        population = sorted(population, key=lambda x: x[1].score)
        survivors = population[: max(2, int(len(population) * 0.3))]

        new_population = survivors.copy()
        while len(new_population) < population_size:
            p1 = random.choice(survivors)[0]
            p2 = random.choice(survivors)[0]
            child = crossover(p1, p2, beverage_type)
            child = mutate(child, beverage_type, mutation_rate=0.20)
            _, child_summary = evaluate(child, beverage_type, target_brix, target_sweetness, target_acidity)
            new_population.append((child, child_summary))

        population = new_population

    population = sorted(population, key=lambda x: x[1].score)
    return population[:20]


# =========================================================
# 검증 / 출력
# =========================================================
def validate_formula(summary: FormulaSummary, beverage_type: str) -> Tuple[str, Dict[str, str]]:
    rule = VALIDATION_RANGES.get(beverage_type)
    if not rule:
        return "UNKNOWN", {}

    details = {}
    passed = True

    for metric, (low, high) in rule.items():
        if metric == "Brix":
            val = summary.total_brix
        elif metric == "pH":
            val = summary.total_ph
        elif metric == "Acid":
            val = summary.total_acid
        else:
            continue

        ok = low <= val <= high
        details[metric] = f"{val:.4f} / 기준 {low}~{high} / {'PASS' if ok else 'FAIL'}"
        if not ok:
            passed = False

    return ("PASS" if passed else "FAIL"), details


def render_formula_table(formula_df: pd.DataFrame, beverage_type: str) -> pd.DataFrame:
    if formula_df is None or formula_df.empty:
        return pd.DataFrame()

    df = formula_df.copy()
    summary = calculate_properties(df, beverage_type)

    df["Brix_Contribution_Value"] = df["Usage_%"] * df["Brix"] / 100.0
    df["Acid_Contribution_Value"] = df["Usage_%"] * df["Acidity"] / 100.0
    df["Sweetness_Contribution_Value"] = df["Usage_%"] * df["Sweetness"] / 100.0
    df["Cost_Contribution"] = df["Usage_%"] * df["Cost"] / 100.0

    display_cols = [
        "Ingredient_Name", "Ingredient_Role", "Usage_%", "Cost", "Cost_Contribution",
        "Brix", "Brix_Contribution_Value", "Acidity", "Acid_Contribution_Value",
        "Sweetness", "Sweetness_Contribution_Value", "FlavorContribution", "Purpose"
    ]
    for col in display_cols:
        if col not in df.columns:
            df[col] = ""

    out = df[display_cols].copy()

    total_row = pd.DataFrame([{
        "Ingredient_Name": "TOTAL",
        "Ingredient_Role": "-",
        "Usage_%": round(pd.to_numeric(out["Usage_%"], errors="coerce").fillna(0.0).sum(), 4),
        "Cost": "",
        "Cost_Contribution": round(summary.total_cost, 4),
        "Brix": "",
        "Brix_Contribution_Value": round(summary.total_brix, 4),
        "Acidity": "",
        "Acid_Contribution_Value": round(summary.total_acid, 4),
        "Sweetness": "",
        "Sweetness_Contribution_Value": round(summary.total_sweetness, 4),
        "FlavorContribution": "",
        "Purpose": f"pH={summary.total_ph:.4f}, Score={summary.score:.4f}",
    }])

    out = pd.concat([out, total_row], ignore_index=True)
    return out


def fallback_rd_evaluation(beverage_type: str, flavor_name: str, summary: FormulaSummary, validation_status: str) -> str:
    comments = []

    if summary.total_brix < 5:
        sweet_comment = "감미가 약한 편이다. 당류 또는 고감미료 보정이 필요하다."
    elif summary.total_brix > 13:
        sweet_comment = "당도 체감이 높은 편이다. 점도와 후미를 함께 확인해야 한다."
    else:
        sweet_comment = "감미 밸런스는 대체로 무난한 수준이다."

    if summary.total_acid < 0.08:
        acid_comment = "산미가 다소 약해 향 발현이 둔할 수 있다."
    elif summary.total_acid > 0.30:
        acid_comment = "산미가 강한 편이라 자극감이 커질 수 있다."
    else:
        acid_comment = "산미 수준은 대체로 적절하다."

    if beverage_type == "식물성음료":
        mouthfeel = "식물성음료는 안정제와 분산 안정성이 마우스필에 크게 작용한다."
    elif beverage_type in ["탄산음료", "스포츠음료"]:
        mouthfeel = "청량감과 산미, 잔미의 균형이 마우스필 핵심이다."
    else:
        mouthfeel = "바디감은 당/산/기능성 소재 조합의 영향이 크다."

    flavor_eval = f"{flavor_name} 콘셉트는 {beverage_type} 유형과의 적합성이 양호하다."
    improve = "표준배합 템플릿 범위 안에서 Flavor/Acid/Sweetener 비율을 미세 조정하는 것이 바람직하다."
    overall = f"표준배합 검증 결과는 {validation_status} 이다."

    comments.append("1. 풍미 밸런스 평가: " + flavor_eval)
    comments.append("2. 감미 밸런스 평가: " + sweet_comment)
    comments.append("3. 산미 밸런스 평가: " + acid_comment)
    comments.append("4. 마우스필 평가: " + mouthfeel)
    comments.append("5. 기술적 개선 제안: " + improve)
    comments.append("6. 종합 판정: " + overall)
    return "\n\n".join(comments)


def to_excel_bytes(formula_table: pd.DataFrame, summary: FormulaSummary, validation_status: str, validation_details: Dict[str, str]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        formula_table.to_excel(writer, sheet_name="Formula", index=False)

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
            pd.DataFrame(
                [{"Metric": k, "Detail": v} for k, v in validation_details.items()]
            ).to_excel(writer, sheet_name="Validation", index=False)

    output.seek(0)
    return output.read()


# =========================================================
# 메인 UI
# =========================================================
st.title("AI 음료 신제품 배합비 개발 플랫폼")

with st.sidebar:
    st.header("설정")
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    model_name = st.text_input("OpenAI Model", value="gpt-5.4")
    excel_path = st.text_input("엑셀 파일 경로", value="beverage_AI_DB_v1.xlsx")

    st.markdown("---")
    beverage_type = st.selectbox("음료 유형 선택", UI_BEVERAGE_TYPES)
    target_brix = st.slider("Target Brix", 3.0, 15.0, 11.0, 0.1)
    target_sweetness = st.slider("Target Sweetness", 0.5, 10.0, 7.0, 0.1)
    target_acidity = st.slider("Target Acidity", 0.01, 0.50, 0.22, 0.01)
    population_size = st.slider("Population Size", 50, 1000, 200, 10)
    generations = st.slider("Generations", 5, 100, 20, 1)

    st.markdown("---")
    run_generate = st.button("배합 생성", use_container_width=True)

# DB 로드
db = load_or_build_db(excel_path)
master_df = db["Ingredient_Master"]
prop_df = db["Ingredient_Property"]
flavor_master_df = db["Flavor_Master"]
flavor_map_df = db["Flavor_Ingredient_Map"]
template_df = db["Beverage_Type_Template"]

ingredient_df = merge_ingredient_data(master_df, prop_df)

# OpenAI client 준비
client, client_error = get_openai_client(api_key)

# flavor 목록 준비
trend_flavors = generate_trend_products(beverage_type, api_client=client, model_name=model_name)
if not trend_flavors:
    trend_flavors = TREND_FLAVORS.get(beverage_type, [])[:20]

selected_flavor = st.selectbox("Flavor 선택", trend_flavors if trend_flavors else ["Default Flavor"])

# 표준 배합 미리보기
st.subheader("표준배합비 참고 템플릿")
std_filtered = filter_ingredient_by_flavor(ingredient_df, flavor_map_df, selected_flavor, beverage_type)
std_formula = build_standard_formula_preview(std_filtered, beverage_type)
std_summary = calculate_properties(std_formula, beverage_type) if not std_formula.empty else FormulaSummary(0, 0, 0, 0, 7, 999999)

col_a, col_b, col_c, col_d, col_e = st.columns(5)
col_a.metric("표준 Brix", f"{std_summary.total_brix:.4f}")
col_b.metric("표준 pH", f"{std_summary.total_ph:.4f}")
col_c.metric("표준 Acid", f"{std_summary.total_acid:.4f}")
col_d.metric("표준 Sweetness", f"{std_summary.total_sweetness:.4f}")
col_e.metric("표준 Cost", f"{std_summary.total_cost:.4f}")

std_display = render_formula_table(std_formula, beverage_type)
if not std_display.empty:
    st.dataframe(std_display, use_container_width=True)
else:
    st.info("표준배합 템플릿 표시용 데이터가 충분하지 않아 fallback 상태로 동작 중이다.")

st.markdown("---")

# 원료 DB 500종 생성 / fallback
with st.expander("원재료 DB 상태", expanded=False):
    st.write(f"기본 원료 수: {len(ingredient_df)}")
    st.write("엑셀 또는 fallback 데이터 기준으로 로드됨.")

if run_generate:
    with st.spinner("원료 DB 준비 및 배합 최적화 중..."):
        working_master = master_df.copy()
        working_prop = prop_df.copy()

        # API 기반 보강 시도
        api_generated_df = None
        if client is not None:
            api_generated_df = generate_ingredient_db_with_api(client, model_name, beverage_type, selected_flavor)

        if api_generated_df is not None and not api_generated_df.empty:
            # API 결과를 내부 스키마로 맞춤
            api_generated_df = normalize_columns(api_generated_df)

            if "Ingredient_ID" not in api_generated_df.columns:
                start_id = int(max(working_master["Ingredient_ID"].max(), 0)) + 1
                api_generated_df["Ingredient_ID"] = list(range(start_id, start_id + len(api_generated_df)))

            master_part = api_generated_df.copy()
            for col in ["Sub_Category", "Origin", "Supplier", "Solubility", "Color"]:
                if col not in master_part.columns:
                    master_part[col] = ""
            if "Cost" not in master_part.columns:
                master_part["Cost"] = 1000.0

            master_part = master_part[[
                "Ingredient_ID", "Ingredient_Name", "Category", "Sub_Category",
                "Origin", "Supplier", "Cost", "Solubility", "Color"
            ]].copy()

            prop_part = api_generated_df.copy()
            for col in ["Brix", "pH", "Acidity", "Sweetness", "Brix_Contribution",
                        "Acid_Contribution", "pH_Effect", "pKa1", "pKa2",
                        "Buffer_Capacity", "pH_Model_Type"]:
                if col not in prop_part.columns:
                    prop_part[col] = 0.0 if col != "pH_Model_Type" else "linear"

            prop_part = prop_part[[
                "Ingredient_ID", "Brix", "pH", "Acidity", "Sweetness",
                "Brix_Contribution", "Acid_Contribution", "pH_Effect",
                "pKa1", "pKa2", "Buffer_Capacity", "pH_Model_Type"
            ]].copy()

            working_master = pd.concat([working_master, master_part], ignore_index=True).drop_duplicates(subset=["Ingredient_ID"])
            working_prop = pd.concat([working_prop, prop_part], ignore_index=True).drop_duplicates(subset=["Ingredient_ID"])

        # 500종 확장 fallback
        expanded_master, expanded_prop = expand_to_500_ingredients(working_master, working_prop)
        expanded_ingredient_df = merge_ingredient_data(expanded_master, expanded_prop)

        st.success(f"원료 DB 준비 완료: {len(expanded_ingredient_df)}개")

        filtered_df = filter_ingredient_by_flavor(expanded_ingredient_df, flavor_map_df, selected_flavor, beverage_type)

        if filtered_df.empty:
            st.error("선택한 flavor와 연결되는 원료를 찾지 못했다.")
            st.stop()

        top_results = optimize_formula(
            filtered_df=filtered_df,
            beverage_type=beverage_type,
            target_brix=target_brix,
            target_sweetness=target_sweetness,
            target_acidity=target_acidity,
            population_size=population_size,
            generations=generations,
        )

    if not top_results:
        st.error("최적화 결과가 비어 있다.")
        st.stop()

    st.subheader("Top 20 최적 배합 결과 요약")
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
    st.dataframe(summary_df, use_container_width=True)

    # 최고 배합
    best_formula, best_summary = top_results[0]
    validation_status, validation_details = validate_formula(best_summary, beverage_type)
    formula_table = render_formula_table(best_formula, beverage_type)

    st.subheader("최종 배합표")
    top1, top2, top3, top4, top5, top6 = st.columns(6)
    top1.metric("Brix", f"{best_summary.total_brix:.4f}")
    top2.metric("pH", f"{best_summary.total_ph:.4f}")
    top3.metric("Acid", f"{best_summary.total_acid:.4f}")
    top4.metric("Sweetness", f"{best_summary.total_sweetness:.4f}")
    top5.metric("Cost", f"{best_summary.total_cost:.4f}")
    top6.metric("Validation", validation_status)

    st.dataframe(formula_table, use_container_width=True)

    st.subheader("표준배합 검증")
    if validation_details:
        validation_df = pd.DataFrame([
            {"Metric": k, "Detail": v} for k, v in validation_details.items()
        ])
        st.dataframe(validation_df, use_container_width=True)

    # 그래프
    st.subheader("결과 분포")
    chart_col1, chart_col2, chart_col3 = st.columns(3)
    with chart_col1:
        st.caption("Brix 분포")
        st.bar_chart(summary_df.set_index("Rank")["Brix"])
    with chart_col2:
        st.caption("원가 분포")
        st.bar_chart(summary_df.set_index("Rank")["Cost"])
    with chart_col3:
        st.caption("Score 분포")
        st.bar_chart(summary_df.set_index("Rank")["Score"])

    # AI 평가
    st.subheader("AI 연구원 평가")
    rd_eval_text = None
    if client is not None:
        rd_eval_text = ai_rd_evaluation_with_api(client, model_name, beverage_type, selected_flavor, formula_table, best_summary)

    if not rd_eval_text:
        rd_eval_text = fallback_rd_evaluation(beverage_type, selected_flavor, best_summary, validation_status)

    st.text_area("평가 결과", value=rd_eval_text, height=260)

    # 다운로드
    csv_data = formula_table.to_csv(index=False).encode("utf-8-sig")
    xlsx_data = to_excel_bytes(formula_table, best_summary, validation_status, validation_details)

    dcol1, dcol2 = st.columns(2)
    with dcol1:
        st.download_button(
            "CSV 다운로드",
            data=csv_data,
            file_name=f"formula_{beverage_type}_{selected_flavor.replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with dcol2:
        st.download_button(
            "Excel 다운로드",
            data=xlsx_data,
            file_name=f"formula_{beverage_type}_{selected_flavor.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

# 디버그
with st.expander("디버그 / 로드 상태", expanded=False):
    st.write("API Key 입력 여부:", bool(api_key))
    st.write("OpenAI client 상태:", "OK" if client is not None else f"Fallback ({client_error})")
    st.write("엑셀 경로:", excel_path)
    st.write("Ingredient_Master rows:", len(master_df))
    st.write("Ingredient_Property rows:", len(prop_df))
    st.write("Flavor_Master rows:", len(flavor_master_df))
    st.write("Flavor_Ingredient_Map rows:", len(flavor_map_df))
    st.write("Beverage_Type_Template rows:", len(template_df))
    st.write("Ingredient columns:", list(ingredient_df.columns))
