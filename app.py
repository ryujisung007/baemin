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

st.set_page_config(
    page_title="오픈AI&식품정보원 음료개발 플랫폼",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

INTENSITY_LABELS = {
    1: "매우 약함",
    2: "약함",
    3: "중간",
    4: "강함",
    5: "매우 강함",
}


@dataclass
class FormulaSummary:
    total_brix: float
    total_acid: float
    total_sweetness: float
    total_cost: float
    total_ph: float
    score: float


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


def ensure_formula_schema(df: pd.DataFrame, beverage_type: str) -> pd.DataFrame:
    """
    자동배합비 계산 전에 반드시 필요한 컬럼을 강제로 보정한다.
    """
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

    numeric_cols = [
        "Brix", "pH", "Acidity", "Sweetness", "Cost",
        "Brix_Contribution", "Acid_Contribution", "pH_Effect",
        "Typical_Range_Min", "Typical_Range_Max", "FlavorContribution", "Usage_%"
    ]
    df = enforce_numeric(df, numeric_cols)

    # Ingredient_Role 비어 있으면 Category로 추론
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
    needed_roles = list(TYPE_TEMPLATES.get(beverage_type, {}).keys())

    for role in needed_roles:
        if role in existing_roles:
            continue
        row = {
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
            "Typical_Range_Min": TYPE_TEMPLATES[beverage_type][role][0],
            "Typical_Range_Max": TYPE_TEMPLATES[beverage_type][role][1],
            "FlavorContribution": 0.0,
            "Purpose": role,
            "Usage_%": 0.0,
        }
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    return df.reset_index(drop=True)


def map_intensity_to_value(level: int, low: float, high: float) -> float:
    ratio = {1: 0.10, 2: 0.30, 3: 0.50, 4: 0.75, 5: 0.95}.get(level, 0.50)
    return round(low + (high - low) * ratio, 4)


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
    prop = enforce_numeric(prop, ["Ingredient_ID", "Brix", "pH", "Acidity", "Sweetness",
                                  "Brix_Contribution", "Acid_Contribution", "pH_Effect"])
    return {"Ingredient_Master": master, "Ingredient_Property": prop, "Flavor_Ingredient_Map": flavor_map}


def merge_ingredient_data(master_df: pd.DataFrame, prop_df: pd.DataFrame) -> pd.DataFrame:
    df = pd.merge(master_df, prop_df, on="Ingredient_ID", how="left")
    return ensure_formula_schema(df, "탄산음료")


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
        df = pd.concat([pd.DataFrame([{
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
        }]), df], ignore_index=True)
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
        survivors = population[: max(4, int(len(population) * 0.3))]

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
