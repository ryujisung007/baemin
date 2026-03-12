import io
import json
import math
import os
import random
import re
import base64
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
DEFAULT_EXCEL_PATH = "beverage_AI_DB_v1.xlsx"

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
    return df.rename(columns=rename_map)


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
    try:
        return json.loads(text)
    except Exception:
        pass

    code_block = re.search(r"```json\s*(\{.*?\}|\[.*?\])\s*```", text, re.S)
    if code_block:
        try:
            return json.loads(code_block.group(1))
        except Exception:
            pass

    obj_match = re.search(r"(\{.*\})", text, re.S)
    if obj_match:
        try:
            return json.loads(obj_match.group(1))
        except Exception:
            pass

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
        return OpenAI(api_key=api_key), None
    except Exception as e:
        return None, f"OpenAI 클라이언트 생성 실패: {e}"


# =========================================================
# 샘플 / fallback 데이터
# =========================================================
def build_sample_ingredient_master() -> pd.DataFrame:
    rows = [
        {"Ingredient_ID": 1, "Ingredient_Name": "정제수", "Category": "Water", "Sub_Category": "Base", "Origin": "국내", "Supplier": "Sample", "Cost": 5, "Solubility": "High", "Color": "Clear"},
        {"Ingredient_ID": 2, "Ingredient_Name": "설탕", "Category": "Sugar", "Sub_Category": "Sucrose", "Origin": "수입", "Supplier": "Sample", "Cost": 1200, "Solubility": "High", "Color": "White"},
        {"Ingredient_ID": 3, "Ingredient_Name": "액상과당", "Category": "Sugar", "Sub_Category": "HFCS", "Origin": "국내", "Supplier": "Sample", "Cost": 900, "Solubility": "High", "Color": "Clear"},
        {"Ingredient_ID": 4, "Ingredient_Name": "수크랄로스", "Category": "Sweetener", "Sub_Category": "HighIntensity", "Origin": "수입", "Supplier": "Sample", "Cost": 150000, "Solubility": "High", "Color": "White"},
        {"Ingredient_ID": 5, "Ingredient_Name": "아세설팜K", "Category": "Sweetener", "Sub_Category": "HighIntensity", "Origin": "수입", "Supplier": "Sample", "Cost": 98000, "Solubility": "High", "Color": "White"},
        {"Ingredient_ID": 6, "Ingredient_Name": "구연산", "Category": "Acid", "Sub_Category": "Citric", "Origin": "수입", "Supplier": "Sample", "Cost": 3500, "Solubility": "High", "Color": "White"},
        {"Ingredient_ID": 7, "Ingredient_Name": "사과산", "Category": "Acid", "Sub_Category": "Malic", "Origin": "수입", "Supplier": "Sample", "Cost": 4200, "Solubility": "High", "Color": "White"},
        {"Ingredient_ID": 8, "Ingredient_Name": "인산", "Category": "Acid", "Sub_Category": "Phosphoric", "Origin": "수입", "Supplier": "Sample", "Cost": 2800, "Solubility": "High", "Color": "Clear"},
        {"Ingredient_ID": 9, "Ingredient_Name": "녹차추출물", "Category": "Extract", "Sub_Category": "Tea", "Origin": "국내", "Supplier": "Sample", "Cost": 45000, "Solubility": "Medium", "Color": "Brown"},
        {"Ingredient_ID": 10, "Ingredient_Name": "생강추출물", "Category": "Extract", "Sub_Category": "Spice", "Origin": "국내", "Supplier": "Sample", "Cost": 38000, "Solubility": "Medium", "Color": "Yellow"},
        {"Ingredient_ID": 11, "Ingredient_Name": "히비스커스추출물", "Category": "Extract", "Sub_Category": "Botanical", "Origin": "수입", "Supplier": "Sample", "Cost": 41000, "Solubility": "Medium", "Color": "Red"},
        {"Ingredient_ID": 12, "Ingredient_Name": "레몬농축액", "Category": "Concentrate", "Sub_Category": "Citrus", "Origin": "수입", "Supplier": "Sample", "Cost": 8000, "Solubility": "High", "Color": "Yellow"},
        {"Ingredient_ID": 13, "Ingredient_Name": "오렌지농축액", "Category": "Concentrate", "Sub_Category": "Citrus", "Origin": "수입", "Supplier": "Sample", "Cost": 7000, "Solubility": "High", "Color": "Orange"},
        {"Ingredient_ID": 14, "Ingredient_Name": "사과농축액", "Category": "Concentrate", "Sub_Category": "Fruit", "Origin": "수입", "Supplier": "Sample", "Cost": 6500, "Solubility": "High", "Color": "Amber"},
        {"Ingredient_ID": 15, "Ingredient_Name": "망고농축액", "Category": "Concentrate", "Sub_Category": "Tropical", "Origin": "수입", "Supplier": "Sample", "Cost": 8200, "Solubility": "High", "Color": "Orange"},
        {"Ingredient_ID": 16, "Ingredient_Name": "복숭아농축액", "Category": "Concentrate", "Sub_Category": "StoneFruit", "Origin": "수입", "Supplier": "Sample", "Cost": 7800, "Solubility": "High", "Color": "Orange"},
        {"Ingredient_ID": 17, "Ingredient_Name": "포도농축액", "Category": "Concentrate", "Sub_Category": "Berry", "Origin": "수입", "Supplier": "Sample", "Cost": 7200, "Solubility": "High", "Color": "Purple"},
        {"Ingredient_ID": 18, "Ingredient_Name": "파인애플농축액", "Category": "Concentrate", "Sub_Category": "Tropical", "Origin": "수입", "Supplier": "Sample", "Cost": 7500, "Solubility": "High", "Color": "Yellow"},
        {"Ingredient_ID": 19, "Ingredient_Name": "펙틴", "Category": "Stabilizer", "Sub_Category": "Hydrocolloid", "Origin": "수입", "Supplier": "Sample", "Cost": 22000, "Solubility": "Medium", "Color": "White"},
        {"Ingredient_ID": 20, "Ingredient_Name": "잔탄검", "Category": "Stabilizer", "Sub_Category": "Hydrocolloid", "Origin": "수입", "Supplier": "Sample", "Cost": 18000, "Solubility": "Medium", "Color": "Cream"},
        {"Ingredient_ID": 21, "Ingredient_Name": "카라멜색소", "Category": "Color", "Sub_Category": "Brown", "Origin": "국내", "Supplier": "Sample", "Cost": 6000, "Solubility": "High", "Color": "Brown"},
        {"Ingredient_ID": 22, "Ingredient_Name": "베타카로틴", "Category": "Color", "Sub_Category": "Orange", "Origin": "수입", "Supplier": "Sample", "Cost": 50000, "Solubility": "Low", "Color": "Orange"},
        {"Ingredient_ID": 23, "Ingredient_Name": "안토시아닌색소", "Category": "Color", "Sub_Category": "RedPurple", "Origin": "수입", "Supplier": "Sample", "Cost": 47000, "Solubility": "Medium", "Color": "Purple"},
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

        keyword_items = []
        if any(k in flavor_l for k in ["lemon", "lime", "yuzu", "citrus"]):
            keyword_items += [("레몬농축액", "Concentrate", 0.5, 12.0, "Flavor")]
        if "orange" in flavor_l or "grapefruit" in flavor_l:
            keyword_items += [("오렌지농축액", "Concentrate", 0.5, 15.0, "Flavor")]
        if "apple" in flavor_l:
            keyword_items += [("사과농축액", "Concentrate", 0.5, 15.0, "Flavor")]
        if any(k in flavor_l for k in ["mango", "tropical"]):
            keyword_items += [("망고농축액", "Concentrate", 0.5, 18.0, "Flavor")]
        if "peach" in flavor_l:
            keyword_items += [("복숭아농축액", "Concentrate", 0.5, 15.0, "Flavor")]
        if any(k in flavor_l for k in ["berry", "grape", "hibiscus"]):
            keyword_items += [("포도농축액", "Concentrate", 0.5, 15.0, "Flavor"),
                              ("히비스커스추출물", "Extract", 0.02, 0.30, "Flavor")]
        if "pineapple" in flavor_l:
            keyword_items += [("파인애플농축액", "Concentrate", 0.5, 15.0, "Flavor")]
        if "ginger" in flavor_l:
            keyword_items += [("생강추출물", "Extract", 0.01, 0.20, "Flavor")]
        if "matcha" in flavor_l:
            keyword_items += [("녹차추출물", "Extract", 0.05, 0.30, "Flavor")]

        for ing_name, role, min_v, max_v, func in default_items + keyword_items:
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


def build_random_recommendations(beverage_type: str, n: int = 10) -> List[str]:
    pool = TREND_FLAVORS.get(beverage_type, [])
    if not pool:
        return []
    n = min(n, len(pool))
    return random.sample(pool, n)


def recommendation_reason(beverage_type: str, flavor_name: str) -> str:
    name_l = flavor_name.lower()
    reason_parts = []

    if beverage_type == "탄산음료":
        reason_parts.append("청량감과 즉시 인지되는 향미가 잘 맞는 조합")
    elif beverage_type == "과채음료":
        reason_parts.append("과즙 콘셉트와 자연스러운 풍미 스토리 구성이 쉬운 조합")
    elif beverage_type == "스포츠음료":
        reason_parts.append("가볍고 빠르게 인지되는 향이라 전해질 음료에 적용성이 높음")
    elif beverage_type == "에너지음료":
        reason_parts.append("강한 첫인상과 기능성 음료 이미지 연출이 쉬운 조합")
    elif beverage_type == "식물성음료":
        reason_parts.append("식물성 베이스의 바디감과 결합하기 쉬운 풍미 방향")
    elif beverage_type == "기능성음료":
        reason_parts.append("기능성 원료의 이취를 완화하거나 건강 이미지를 강화하기 좋은 조합")

    if any(k in name_l for k in ["lemon", "lime", "yuzu", "citrus", "orange", "grapefruit"]):
        reason_parts.append("시트러스 계열이라 산미 설계와 향 발현이 직관적임")
    if any(k in name_l for k in ["mango", "pineapple", "guava", "passionfruit", "tropical"]):
        reason_parts.append("트로피컬 계열이라 트렌디하고 시각적 임팩트가 큼")
    if any(k in name_l for k in ["berry", "grape", "hibiscus", "pomegranate", "lychee"]):
        reason_parts.append("컬러 마케팅과 프리미엄 이미지를 만들기 쉬움")
    if any(k in name_l for k in ["ginger", "mint", "cucumber"]):
        reason_parts.append("차별화 포인트가 분명해 신제품 스토리텔링에 유리함")
    if any(k in name_l for k in ["vanilla", "chocolate", "banana", "matcha", "coffee"]):
        reason_parts.append("부드러운 바디감과 연결되어 식물성 또는 디저트형 콘셉트에 적합함")

    return " / ".join(reason_parts[:3]) if reason_parts else "해당 음료유형의 최근 풍미 확장 방향과 잘 맞는 조합"


def build_image_prompt(product_name: str, beverage_type: str, formula_df: pd.DataFrame) -> str:
    if formula_df is None or formula_df.empty:
        return f"""
Create a premium beverage product rendering.
Product name: {product_name}
Beverage type: {beverage_type}
Show one hero packshot on a clean studio background.
Modern Korean market packaging style, photorealistic, high detail.
""".strip()

    top_ings = (
        formula_df[formula_df["Ingredient_Role"] != "Water"]
        .sort_values("Usage_%", ascending=False)
        .head(5)["Ingredient_Name"]
        .astype(str)
        .tolist()
    )
    ing_text = ", ".join(top_ings)

    return f"""
Create a premium commercial beverage product image.
Product name: {product_name}
Beverage type: {beverage_type}
Key ingredients/flavor cues: {ing_text}

Requirements:
- photorealistic beverage product rendering
- one hero bottle/can/package in front view
- ingredient cues reflected visually in color and garnish
- clean premium studio lighting
- Korean retail-ready modern packaging feeling
- no extra text except product name on pack
- high detail, appetizing, realistic liquid appearance
""".strip()


# =========================================================
# 엑셀 로드 / fallback
# =========================================================
@st.cache_data(show_spinner=False)
def load_or_build_db() -> Dict[str, pd.DataFrame]:
    result: Dict[str, pd.DataFrame] = {}

    if os.path.exists(DEFAULT_EXCEL_PATH):
        try:
            xls = pd.ExcelFile(DEFAULT_EXCEL_PATH)
            for sheet in xls.sheet_names:
                try:
                    result[sheet] = normalize_columns(pd.read_excel(xls, sheet_name=sheet))
                except Exception:
                    continue
        except Exception:
            result = {}

    master = None
    prop = None
    flavor_master = None
    flavor_map = None
    beverage_template = None

    for _, df in result.items():
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
# OpenAI 함수
# =========================================================
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
            if getattr(item, "url", None):
                return None
        return None
    except Exception:
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

    df = ingredient_df.merge(
        matched[["Ingredient_Name", "Ingredient_Role", "Typical_Range_Min", "Typical_Range_Max", "Function"]],
        on="Ingredient_Name",
        how="inner",
    )

    if df.empty:
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


# =========================================================
# 계산
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


def calculate_properties(formula_df: pd.DataFrame, beverage_type: str) -> FormulaSummary:
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
    return rebalance_water(individual, beverage_type)


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

    return rebalance_water(pd.DataFrame(rows), beverage_type)


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

    return rebalance_water(df, beverage_type)


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
        _, summary = evaluate(indiv, beverage_type, target_brix, target_sweetness, target_acidity)
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

    return pd.concat([out, total_row], ignore_index=True)


def fallback_rd_evaluation(beverage_type: str, flavor_name: str, summary: FormulaSummary, validation_status: str) -> str:
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

    return "\n\n".join([
        f"1. 풍미 밸런스 평가: {flavor_name} 콘셉트는 {beverage_type} 유형과의 적합성이 양호하다.",
        f"2. 감미 밸런스 평가: {sweet_comment}",
        f"3. 산미 밸런스 평가: {acid_comment}",
        f"4. 마우스필 평가: {mouthfeel}",
        "5. 기술적 개선 제안: 표준배합 템플릿 범위 안에서 Flavor/Acid/Sweetener 비율을 미세 조정하는 것이 바람직하다.",
        f"6. 종합 판정: 표준배합 검증 결과는 {validation_status} 이다.",
    ])


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
# 앱 시작
# =========================================================
st.title("AI 음료 신제품 배합비 개발 플랫폼")

db = load_or_build_db()
master_df = db["Ingredient_Master"]
prop_df = db["Ingredient_Property"]
flavor_master_df = db["Flavor_Master"]
flavor_map_df = db["Flavor_Ingredient_Map"]
template_df = db["Beverage_Type_Template"]
ingredient_df = merge_ingredient_data(master_df, prop_df)

# session state 초기화
if "last_beverage_type" not in st.session_state:
    st.session_state.last_beverage_type = UI_BEVERAGE_TYPES[0]

if "recommended_flavors" not in st.session_state:
    st.session_state.recommended_flavors = build_random_recommendations(UI_BEVERAGE_TYPES[0], 10)

if "selected_flavor" not in st.session_state:
    st.session_state.selected_flavor = st.session_state.recommended_flavors[0] if st.session_state.recommended_flavors else ""

if "target_brix" not in st.session_state:
    st.session_state.target_brix = 11.0
if "target_sweetness" not in st.session_state:
    st.session_state.target_sweetness = 7.0
if "target_acidity" not in st.session_state:
    st.session_state.target_acidity = 0.22

with st.sidebar:
    st.header("설정")
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    model_name = st.text_input("OpenAI Model", value="gpt-5.4")
    image_model_name = st.text_input("Image Model", value="gpt-image-1")

    st.markdown("---")
    beverage_type = st.selectbox("음료 유형 선택", UI_BEVERAGE_TYPES)

    # 유형 변경 시 랜덤추천과 슬라이더 기본값 갱신
    if beverage_type != st.session_state.last_beverage_type:
        st.session_state.last_beverage_type = beverage_type
        st.session_state.recommended_flavors = build_random_recommendations(beverage_type, 10)
        st.session_state.selected_flavor = st.session_state.recommended_flavors[0] if st.session_state.recommended_flavors else ""

        tmp_flavor = st.session_state.selected_flavor
        tmp_filtered = filter_ingredient_by_flavor(ingredient_df, flavor_map_df, tmp_flavor, beverage_type)
        tmp_std_formula = build_standard_formula_preview(tmp_filtered, beverage_type)
        tmp_std_summary = calculate_properties(tmp_std_formula, beverage_type) if not tmp_std_formula.empty else FormulaSummary(11.0, 0.22, 7.0, 0, 4.0, 0)

        st.session_state.target_brix = round(tmp_std_summary.total_brix, 2)
        st.session_state.target_sweetness = round(clamp(tmp_std_summary.total_sweetness, 0.5, 10.0), 2)
        st.session_state.target_acidity = round(clamp(tmp_std_summary.total_acid, 0.01, 0.50), 2)

    selected_flavor = st.selectbox(
        "추천 제품명/Flavor 선택",
        st.session_state.recommended_flavors if st.session_state.recommended_flavors else [""],
        key="selected_flavor",
    )

    target_brix = st.slider(
        "Target Brix",
        3.0,
        15.0,
        float(clamp(st.session_state.target_brix, 3.0, 15.0)),
        0.1,
        key="target_brix",
    )
    target_sweetness = st.slider(
        "Target Sweetness",
        0.5,
        10.0,
        float(clamp(st.session_state.target_sweetness, 0.5, 10.0)),
        0.1,
        key="target_sweetness",
    )
    target_acidity = st.slider(
        "Target Acidity",
        0.01,
        0.50,
        float(clamp(st.session_state.target_acidity, 0.01, 0.50)),
        0.01,
        key="target_acidity",
    )

    population_size = st.slider("Population Size", 50, 1000, 200, 10)
    generations = st.slider("Generations", 5, 100, 20, 1)

    st.markdown("---")
    run_generate = st.button("배합 생성", use_container_width=True)
    run_image = st.button("이미지 출력", use_container_width=True)

client, client_error = get_openai_client(api_key)

# 랜덤 추천 10개 + 이유
st.subheader("랜덤 트렌드 추천 10선")
rec_rows = []
for flavor in st.session_state.recommended_flavors:
    rec_rows.append({
        "추천 제품명": flavor,
        "추천 이유": recommendation_reason(beverage_type, flavor),
    })
st.dataframe(pd.DataFrame(rec_rows), use_container_width=True)

# 표준배합 미리보기
std_filtered = filter_ingredient_by_flavor(ingredient_df, flavor_map_df, selected_flavor, beverage_type)
std_formula = build_standard_formula_preview(std_filtered, beverage_type)
std_summary = calculate_properties(std_formula, beverage_type) if not std_formula.empty else FormulaSummary(0, 0, 0, 0, 7, 999999)

st.subheader("표준배합비 참고 템플릿")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("표준 Brix", f"{std_summary.total_brix:.4f}")
c2.metric("표준 pH", f"{std_summary.total_ph:.4f}")
c3.metric("표준 Acid", f"{std_summary.total_acid:.4f}")
c4.metric("표준 Sweetness", f"{std_summary.total_sweetness:.4f}")
c5.metric("표준 Cost", f"{std_summary.total_cost:.4f}")

std_display = render_formula_table(std_formula, beverage_type)
if not std_display.empty:
    st.dataframe(std_display, use_container_width=True)
else:
    st.info("표준배합 템플릿 표시용 데이터가 충분하지 않다.")

st.markdown("---")

best_formula = None
best_summary = None
formula_table = None
validation_status = None
validation_details = None

if run_generate:
    filtered_df = filter_ingredient_by_flavor(ingredient_df, flavor_map_df, selected_flavor, beverage_type)

    if filtered_df.empty:
        st.error("선택한 flavor와 연결되는 원료를 찾지 못했다.")
        st.stop()

    with st.spinner("배합 최적화 중..."):
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

    best_formula, best_summary = top_results[0]
    validation_status, validation_details = validate_formula(best_summary, beverage_type)
    formula_table = render_formula_table(best_formula, beverage_type)

    st.subheader("최종 배합표")
    t1, t2, t3, t4, t5, t6 = st.columns(6)
    t1.metric("Brix", f"{best_summary.total_brix:.4f}")
    t2.metric("pH", f"{best_summary.total_ph:.4f}")
    t3.metric("Acid", f"{best_summary.total_acid:.4f}")
    t4.metric("Sweetness", f"{best_summary.total_sweetness:.4f}")
    t5.metric("Cost", f"{best_summary.total_cost:.4f}")
    t6.metric("Validation", validation_status)

    st.dataframe(formula_table, use_container_width=True)

    st.subheader("표준배합 검증")
    if validation_details:
        validation_df = pd.DataFrame([
            {"Metric": k, "Detail": v} for k, v in validation_details.items()
        ])
        st.dataframe(validation_df, use_container_width=True)

    st.subheader("결과 분포")
    gc1, gc2, gc3 = st.columns(3)
    with gc1:
        st.caption("Brix 분포")
        st.bar_chart(summary_df.set_index("Rank")["Brix"])
    with gc2:
        st.caption("원가 분포")
        st.bar_chart(summary_df.set_index("Rank")["Cost"])
    with gc3:
        st.caption("Score 분포")
        st.bar_chart(summary_df.set_index("Rank")["Score"])

    st.subheader("AI 연구원 평가")
    rd_eval_text = None
    if client is not None:
        rd_eval_text = ai_rd_evaluation_with_api(client, model_name, beverage_type, selected_flavor, formula_table, best_summary)
    if not rd_eval_text:
        rd_eval_text = fallback_rd_evaluation(beverage_type, selected_flavor, best_summary, validation_status)
    st.text_area("평가 결과", value=rd_eval_text, height=260)

    csv_data = formula_table.to_csv(index=False).encode("utf-8-sig")
    xlsx_data = to_excel_bytes(formula_table, best_summary, validation_status, validation_details)

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

# 이미지 생성 버튼
st.subheader("제품 이미지 생성")
if run_image:
    if client is None:
        st.error("이미지 생성을 위해 OpenAI API Key가 필요하다.")
    else:
        current_formula = best_formula if best_formula is not None else std_formula
        image_prompt = build_image_prompt(selected_flavor, beverage_type, current_formula)

        with st.spinner("이미지 생성 중..."):
            image_bytes = generate_image_with_openai(client, image_prompt, image_model_name)

        if image_bytes:
            st.image(image_bytes, caption=f"{selected_flavor} 이미지", use_container_width=True)
        else:
            st.error("이미지 생성에 실패했다. 모델명/API 권한/요청 제한을 확인해라.")

with st.expander("디버그 / 로드 상태", expanded=False):
    st.write("API Key 입력 여부:", bool(api_key))
    st.write("OpenAI client 상태:", "OK" if client is not None else f"Fallback ({client_error})")
    st.write("기본 엑셀 파일 존재 여부:", os.path.exists(DEFAULT_EXCEL_PATH))
    st.write("Ingredient_Master rows:", len(master_df))
    st.write("Ingredient_Property rows:", len(prop_df))
    st.write("Flavor_Master rows:", len(flavor_master_df))
    st.write("Flavor_Ingredient_Map rows:", len(flavor_map_df))
    st.write("Beverage_Type_Template rows:", len(template_df))
    st.write("Ingredient columns:", list(ingredient_df.columns))
