import streamlit as st
import pandas as pd
import numpy as np
import json
import re
import random
import io

# ──────────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────────
st.set_page_config(page_title="AI 음료 배합비 개발", layout="wide")

# ──────────────────────────────────────────────
# 1. 음료유형별 표준 배합비 데이터 (하드코딩)
# ──────────────────────────────────────────────
STANDARD_TEMPLATES = {
    "탄산음료": {
        "Brix": (8.0, 12.0, 10.0),
        "pH": (2.5, 4.5, 3.5),
        "산도(%)": (0.10, 0.30, 0.18),
        "감미도": (0.8, 1.4, 1.0),
        "roles": {
            "정제수": (85, 90), "당류": (8, 12), "산미료": (0.10, 0.30),
            "향료": (0.05, 0.20), "색소": (0.001, 0.01), "감미료": (0, 0.03),
        },
    },
    "과채음료": {
        "Brix": (8.0, 14.0, 11.0),
        "pH": (2.5, 4.5, 3.6),
        "산도(%)": (0.10, 0.35, 0.20),
        "감미도": (0.8, 1.5, 1.1),
        "roles": {
            "정제수": (60, 80), "농축과즙": (10, 30), "당류": (5, 10),
            "산미료": (0.10, 0.30), "향료": (0.05, 0.15), "안정제": (0.05, 0.20),
        },
    },
    "스포츠음료": {
        "Brix": (4.0, 7.0, 6.0),
        "pH": (3.0, 4.5, 3.5),
        "산도(%)": (0.05, 0.20, 0.10),
        "감미도": (0.5, 1.0, 0.7),
        "roles": {
            "정제수": (90, 94), "당류": (4, 6), "전해질": (0.10, 0.30),
            "산미료": (0.05, 0.15), "향료": (0.05, 0.10),
        },
    },
    "에너지음료": {
        "Brix": (10.0, 14.0, 12.0),
        "pH": (2.5, 4.0, 3.2),
        "산도(%)": (0.10, 0.30, 0.20),
        "감미도": (1.0, 1.5, 1.2),
        "roles": {
            "정제수": (85, 90), "당류": (10, 12), "타우린": (0.3, 0.4),
            "카페인": (0.02, 0.04), "비타민": (0.01, 0.05), "산미료": (0.10, 0.25),
        },
    },
    "기타음료": {
        "Brix": (5.0, 12.0, 8.0),
        "pH": (3.0, 7.0, 4.5),
        "산도(%)": (0.05, 0.30, 0.15),
        "감미도": (0.5, 1.5, 1.0),
        "roles": {
            "정제수": (80, 92), "당류": (5, 12), "산미료": (0.05, 0.30),
            "향료": (0.05, 0.20), "기능성원료": (0.1, 2.0),
        },
    },
}

# ──────────────────────────────────────────────
# 2. 음료유형별 트렌드 Flavor 20개
# ──────────────────────────────────────────────
TREND_FLAVORS = {
    "탄산음료": [
        "Classic Cola", "Lemon Lime", "Grapefruit Citrus", "Blood Orange",
        "Yuzu Citrus", "Ginger Ale", "Pineapple Soda", "Mango Sparkling",
        "Peach Sparkling", "Apple Soda", "Berry Mix", "Strawberry Lime",
        "Watermelon Soda", "Lychee Sparkling", "Passionfruit Soda",
        "Guava Sparkling", "Lemon Mint Soda", "Hibiscus Berry",
        "Cucumber Lime", "Elderflower Citrus",
    ],
    "과채음료": [
        "Mango Orange", "Peach Mango", "Apple Mango", "Apple Peach",
        "Grape Berry", "Pineapple Coconut", "Strawberry Banana",
        "Mango Passionfruit", "Orange Carrot", "Apple Kiwi",
        "Peach Guava", "Berry Pomegranate", "Apple Ginger", "Lemon Honey",
        "Mango Aloe", "Peach Aloe", "Apple Hibiscus", "Pineapple Mint",
        "Strawberry Lychee", "Mango Dragonfruit",
    ],
    "스포츠음료": [
        "Lemon Lime Electrolyte", "Orange Electrolyte", "Citrus Mix",
        "Grapefruit Electrolyte", "Lemon Honey", "Mango Electrolyte",
        "Peach Electrolyte", "Berry Electrolyte", "Tropical Electrolyte",
        "Watermelon Electrolyte", "Coconut Electrolyte",
        "Pineapple Electrolyte", "Apple Electrolyte", "Lychee Electrolyte",
        "Passionfruit Electrolyte", "Guava Electrolyte", "Lemon Ginger",
        "Berry Citrus", "Cucumber Lime", "Aloe Citrus",
    ],
    "에너지음료": [
        "Classic Energy Citrus", "Tropical Energy", "Mango Energy",
        "Peach Energy", "Berry Energy", "Watermelon Energy", "Apple Energy",
        "Pineapple Energy", "Dragonfruit Energy", "Guava Energy",
        "Lychee Energy", "Passionfruit Energy", "Lemon Energy", "Lime Energy",
        "Grapefruit Energy", "Yuzu Energy", "Mango Peach Energy",
        "Berry Blast Energy", "Citrus Punch Energy", "Tropical Punch Energy",
    ],
    "기타음료": [
        "Lemon Vitamin", "Orange Vitamin", "Berry Vitamin", "Mango Vitamin",
        "Pineapple Vitamin", "Apple Fiber", "Berry Fiber", "Lemon Collagen",
        "Peach Collagen", "Mango Collagen", "Apple Probiotic",
        "Berry Probiotic", "Lemon Ginger", "Apple Ginger", "Honey Lemon",
        "Yuzu Honey", "Aloe Mango", "Aloe Peach", "Hibiscus Berry",
        "Pomegranate Antioxidant",
    ],
}

# ──────────────────────────────────────────────
# 3. 세션 상태 초기화
# ──────────────────────────────────────────────
for key in ["ingredient_db", "formula_result", "ai_evaluation"]:
    if key not in st.session_state:
        st.session_state[key] = None


# ──────────────────────────────────────────────
# 4. OpenAI 클라이언트 헬퍼
# ──────────────────────────────────────────────
def get_openai_client(api_key):
    """OpenAI 클라이언트를 안전하게 생성한다."""
    if not api_key or len(api_key.strip()) < 10:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key.strip())
    except Exception:
        return None


def call_openai_json(client, system_msg, user_msg, fallback=None):
    """OpenAI API를 호출하고 JSON 파싱까지 수행한다.
    실패 시 fallback 값을 반환한다."""
    if client is None:
        return fallback
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=4000,
        )
        text = resp.choices[0].message.content
        data = json.loads(text)
        return data
    except Exception:
        # fallback: regex로 JSON 배열 추출 시도
        try:
            text = resp.choices[0].message.content
            match = re.search(r"\[.*\]", text, re.S)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return fallback


def call_openai_text(client, system_msg, user_msg, fallback="평가를 생성할 수 없습니다."):
    """OpenAI API를 호출하고 텍스트를 반환한다."""
    if client is None:
        return fallback
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.5,
            max_tokens=2000,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"{fallback}\n(오류: {e})"


# ──────────────────────────────────────────────
# 5. 원료 DB 생성 함수
# ──────────────────────────────────────────────
def generate_ingredient_db_via_api(client, beverage_type, flavor):
    """ChatGPT API로 선택된 음료유형+Flavor 기반 원료 DB를 생성한다."""
    prompt = f"""
You are a beverage R&D scientist.
Create an ingredient database for a "{beverage_type}" beverage with "{flavor}" flavor.

Return a JSON object with key "ingredients" containing an array.
Each element must have EXACTLY these fields:
  "Ingredient": ingredient name (Korean preferred),
  "Category": one of (당류,산미료,감미료,농축액,추출물,안정제,색소,비타민,전해질,향료,기능성원료,기타),
  "Brix": number (0-100),
  "pH": number (1-8),
  "Acidity": number (0-100, as %),
  "Sweetness": number (relative to sucrose=1.0, e.g. sucralose=600),
  "Cost": number (KRW per kg),
  "Purpose": short description of purpose in Korean,
  "FlavorContribution": one of (Sweet,Sour,Bitter,Citrus,Fruity,Floral,Neutral,Texture,Color,Functional)

Create exactly 30 ingredients appropriate for {beverage_type} + {flavor}.
Include: water, sugars, acids, concentrates, flavors, stabilizers, colors.
Return ONLY the JSON object, nothing else.
"""
    data = call_openai_json(
        client,
        "You are a beverage R&D scientist. Always respond in valid JSON.",
        prompt,
        fallback=None,
    )
    if data and "ingredients" in data:
        try:
            df = pd.DataFrame(data["ingredients"])
            # 타입 안전 보정
            for col in ["Brix", "pH", "Acidity", "Sweetness", "Cost"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            return df
        except Exception:
            return None
    return None


def get_builtin_ingredient_db(beverage_type, flavor):
    """API 실패 시 사용하는 내장 원료 DB (최소 20종)."""
    base = [
        {"Ingredient": "정제수", "Category": "기타", "Brix": 0, "pH": 7.0, "Acidity": 0, "Sweetness": 0, "Cost": 0, "Purpose": "용매/베이스", "FlavorContribution": "Neutral"},
        {"Ingredient": "백설탕", "Category": "당류", "Brix": 99.9, "pH": 7.0, "Acidity": 0, "Sweetness": 1.0, "Cost": 1200, "Purpose": "감미 부여", "FlavorContribution": "Sweet"},
        {"Ingredient": "액상과당(HFCS55)", "Category": "당류", "Brix": 77.0, "pH": 4.0, "Acidity": 0.1, "Sweetness": 1.2, "Cost": 1000, "Purpose": "감미 부여", "FlavorContribution": "Sweet"},
        {"Ingredient": "구연산", "Category": "산미료", "Brix": 0, "pH": 2.2, "Acidity": 100, "Sweetness": 0, "Cost": 2800, "Purpose": "산도 조절", "FlavorContribution": "Sour"},
        {"Ingredient": "사과산", "Category": "산미료", "Brix": 0, "pH": 2.8, "Acidity": 90, "Sweetness": 0, "Cost": 4000, "Purpose": "산미 부여", "FlavorContribution": "Sour"},
        {"Ingredient": "구연산나트륨", "Category": "산미료", "Brix": 0, "pH": 8.0, "Acidity": 0, "Sweetness": 0, "Cost": 3500, "Purpose": "pH 완충", "FlavorContribution": "Neutral"},
        {"Ingredient": "아스파탐", "Category": "감미료", "Brix": 0, "pH": 5.0, "Acidity": 0, "Sweetness": 200, "Cost": 35000, "Purpose": "고감미 부여", "FlavorContribution": "Sweet"},
        {"Ingredient": "수크랄로스", "Category": "감미료", "Brix": 0, "pH": 7.0, "Acidity": 0, "Sweetness": 600, "Cost": 180000, "Purpose": "고감미 부여", "FlavorContribution": "Sweet"},
        {"Ingredient": "스테비올배당체", "Category": "감미료", "Brix": 0, "pH": 5.5, "Acidity": 0, "Sweetness": 300, "Cost": 95000, "Purpose": "천연감미 부여", "FlavorContribution": "Sweet"},
        {"Ingredient": "에리스리톨", "Category": "당류", "Brix": 99.5, "pH": 7.0, "Acidity": 0, "Sweetness": 0.65, "Cost": 8000, "Purpose": "벌크감미/저칼로리", "FlavorContribution": "Sweet"},
        {"Ingredient": "오렌지농축과즙", "Category": "농축액", "Brix": 65, "pH": 3.5, "Acidity": 4.5, "Sweetness": 0.8, "Cost": 3500, "Purpose": "과일풍미", "FlavorContribution": "Fruity"},
        {"Ingredient": "사과농축과즙", "Category": "농축액", "Brix": 70, "pH": 3.4, "Acidity": 3.0, "Sweetness": 0.9, "Cost": 3000, "Purpose": "과일풍미", "FlavorContribution": "Fruity"},
        {"Ingredient": "레몬농축과즙", "Category": "농축액", "Brix": 50, "pH": 2.2, "Acidity": 6.5, "Sweetness": 0.3, "Cost": 4000, "Purpose": "시트러스풍미", "FlavorContribution": "Citrus"},
        {"Ingredient": "망고농축과즙", "Category": "농축액", "Brix": 65, "pH": 4.0, "Acidity": 1.5, "Sweetness": 0.9, "Cost": 5500, "Purpose": "과일풍미", "FlavorContribution": "Fruity"},
        {"Ingredient": "복숭아농축과즙", "Category": "농축액", "Brix": 65, "pH": 3.8, "Acidity": 1.8, "Sweetness": 0.85, "Cost": 4500, "Purpose": "과일풍미", "FlavorContribution": "Fruity"},
        {"Ingredient": "포도농축과즙", "Category": "농축액", "Brix": 68, "pH": 3.3, "Acidity": 5.0, "Sweetness": 0.85, "Cost": 4000, "Purpose": "과일풍미", "FlavorContribution": "Fruity"},
        {"Ingredient": "비타민C", "Category": "비타민", "Brix": 0, "pH": 2.5, "Acidity": 100, "Sweetness": 0, "Cost": 12000, "Purpose": "항산화/영양강화", "FlavorContribution": "Sour"},
        {"Ingredient": "펙틴", "Category": "안정제", "Brix": 0, "pH": 3.5, "Acidity": 0.5, "Sweetness": 0, "Cost": 25000, "Purpose": "점도/안정성", "FlavorContribution": "Texture"},
        {"Ingredient": "카라멜색소", "Category": "색소", "Brix": 0, "pH": 4.5, "Acidity": 0, "Sweetness": 0, "Cost": 5000, "Purpose": "갈색 착색", "FlavorContribution": "Color"},
        {"Ingredient": "베타카로틴", "Category": "색소", "Brix": 0, "pH": 7.0, "Acidity": 0, "Sweetness": 0, "Cost": 15000, "Purpose": "황색 착색", "FlavorContribution": "Color"},
        {"Ingredient": "과일향료", "Category": "향료", "Brix": 0, "pH": 5.5, "Acidity": 0, "Sweetness": 0, "Cost": 20000, "Purpose": "향미 부여", "FlavorContribution": "Fruity"},
        {"Ingredient": "타우린", "Category": "기능성원료", "Brix": 0, "pH": 5.0, "Acidity": 0, "Sweetness": 0, "Cost": 15000, "Purpose": "에너지/기능성", "FlavorContribution": "Functional"},
        {"Ingredient": "카페인", "Category": "기능성원료", "Brix": 0, "pH": 6.0, "Acidity": 0, "Sweetness": 0, "Cost": 25000, "Purpose": "각성효과", "FlavorContribution": "Bitter"},
        {"Ingredient": "염화나트륨", "Category": "전해질", "Brix": 0, "pH": 7.0, "Acidity": 0, "Sweetness": 0, "Cost": 500, "Purpose": "전해질 보충", "FlavorContribution": "Neutral"},
        {"Ingredient": "염화칼륨", "Category": "전해질", "Brix": 0, "pH": 7.0, "Acidity": 0, "Sweetness": 0, "Cost": 2000, "Purpose": "전해질 보충", "FlavorContribution": "Neutral"},
    ]
    return pd.DataFrame(base)


# ──────────────────────────────────────────────
# 6. 배합비 생성 알고리즘
# ──────────────────────────────────────────────
def generate_formula(ingredient_db, target_brix, target_acid, target_sweet, beverage_type):
    """원료 DB에서 배합비를 생성하고 Water Balance 적용."""
    template = STANDARD_TEMPLATES.get(beverage_type, STANDARD_TEMPLATES["기타음료"])
    roles = template["roles"]

    # 원료 역할별 선택
    formula_rows = []

    # 정제수 제외한 원료 선택
    db = ingredient_db.copy()
    water_row = db[db["Ingredient"].str.contains("정제수|Water|water", na=False)]
    others = db[~db["Ingredient"].str.contains("정제수|Water|water", na=False)]

    # 카테고리별 대표 원료 선택
    categories_needed = ["당류", "산미료", "농축액", "향료"]
    selected_indices = set()

    for cat in categories_needed:
        cat_rows = others[others["Category"] == cat]
        if len(cat_rows) > 0:
            pick = cat_rows.sample(n=min(2, len(cat_rows)), random_state=random.randint(0, 9999))
            selected_indices.update(pick.index.tolist())

    # 감미료 (감미도 > 1인 것)
    sweeteners = others[others["Sweetness"] > 1.5]
    if len(sweeteners) > 0:
        pick = sweeteners.sample(n=1, random_state=random.randint(0, 9999))
        selected_indices.update(pick.index.tolist())

    # 안정제/색소 (선택적)
    for cat in ["안정제", "색소"]:
        cat_rows = others[others["Category"] == cat]
        if len(cat_rows) > 0 and random.random() > 0.3:
            pick = cat_rows.sample(n=1, random_state=random.randint(0, 9999))
            selected_indices.update(pick.index.tolist())

    # 기능성원료 (에너지음료 등)
    if beverage_type in ["에너지음료"]:
        func_rows = others[others["Category"].isin(["기능성원료", "비타민", "전해질"])]
        if len(func_rows) > 0:
            pick = func_rows.sample(n=min(2, len(func_rows)), random_state=random.randint(0, 9999))
            selected_indices.update(pick.index.tolist())

    selected = others.loc[list(selected_indices)].copy()

    # 사용량 할당 (목표값 기반 최적화)
    best_formula = None
    best_score = float("inf")

    for trial in range(500):
        rows = []
        total_non_water = 0.0

        for _, ing in selected.iterrows():
            cat = str(ing.get("Category", ""))
            if cat == "당류":
                usage = random.uniform(3.0, 12.0)
            elif cat == "산미료":
                usage = random.uniform(0.05, 0.35)
            elif cat == "농축액":
                usage = random.uniform(0.5, 5.0)
            elif cat == "감미료":
                usage = random.uniform(0.005, 0.05)
            elif cat in ("안정제", "색소"):
                usage = random.uniform(0.005, 0.1)
            elif cat == "향료":
                usage = random.uniform(0.02, 0.15)
            elif cat in ("기능성원료", "비타민", "전해질"):
                usage = random.uniform(0.01, 0.4)
            else:
                usage = random.uniform(0.01, 1.0)

            total_non_water += usage
            rows.append({"Ingredient": ing["Ingredient"], "Usage": usage, **ing.to_dict()})

        if total_non_water >= 99.5:
            continue

        water_usage = 100.0 - total_non_water
        # 이화학 계산
        total_brix = sum(r["Usage"] * float(r.get("Brix", 0)) / 100.0 for r in rows)
        total_acid = sum(r["Usage"] * float(r.get("Acidity", 0)) / 100.0 for r in rows)
        total_sweet_raw = sum(r["Usage"] * float(r.get("Sweetness", 0)) / 100.0 for r in rows)
        total_cost = sum(r["Usage"] * float(r.get("Cost", 0)) / 100.0 for r in rows)

        score = (
            abs(target_brix - total_brix) * 40
            + abs(target_acid - total_acid) * 80
            + abs(target_sweet - total_sweet_raw) * 30
        )

        if score < best_score:
            best_score = score
            best_formula = {
                "rows": rows,
                "water_usage": water_usage,
                "total_brix": total_brix,
                "total_acid": total_acid,
                "total_sweet": total_sweet_raw,
                "total_cost": total_cost,
                "score": score,
            }

    if best_formula is None:
        return None

    # DataFrame 구성
    result = []
    for r in best_formula["rows"]:
        usage = r["Usage"]
        brix_val = float(r.get("Brix", 0))
        acid_val = float(r.get("Acidity", 0))
        sweet_val = float(r.get("Sweetness", 0))
        cost_val = float(r.get("Cost", 0))
        result.append({
            "원료명": r["Ingredient"],
            "사용량(%)": round(usage, 4),
            "분류": r.get("Category", ""),
            "사용목적": r.get("Purpose", ""),
            "맛기여": r.get("FlavorContribution", ""),
            "Brix기여": round(usage * brix_val / 100, 4),
            "산도기여": round(usage * acid_val / 100, 4),
            "감미도기여": round(usage * sweet_val / 100, 4),
            "원가기여(원/kg)": round(usage * cost_val / 100, 2),
        })

    # 정제수 행 추가
    result.append({
        "원료명": "정제수",
        "사용량(%)": round(best_formula["water_usage"], 4),
        "분류": "기타",
        "사용목적": "용매/베이스",
        "맛기여": "Neutral",
        "Brix기여": 0.0,
        "산도기여": 0.0,
        "감미도기여": 0.0,
        "원가기여(원/kg)": 0.0,
    })

    df = pd.DataFrame(result)

    # TOTAL 행
    total_row = {
        "원료명": "■ TOTAL",
        "사용량(%)": round(df["사용량(%)"].sum(), 2),
        "분류": "",
        "사용목적": "",
        "맛기여": "",
        "Brix기여": round(df["Brix기여"].sum(), 2),
        "산도기여": round(df["산도기여"].sum(), 4),
        "감미도기여": round(df["감미도기여"].sum(), 4),
        "원가기여(원/kg)": round(df["원가기여(원/kg)"].sum(), 2),
    }
    df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)

    return df


# ──────────────────────────────────────────────
# 7. 표준배합 검증
# ──────────────────────────────────────────────
def validate_formula(formula_df, beverage_type):
    """배합비가 표준 범위 내인지 검증한다."""
    tmpl = STANDARD_TEMPLATES.get(beverage_type, STANDARD_TEMPLATES["기타음료"])
    total_row = formula_df[formula_df["원료명"] == "■ TOTAL"]
    if total_row.empty:
        return []

    tr = total_row.iloc[0]
    results = []

    brix_val = float(tr["Brix기여"])
    brix_min, brix_max, _ = tmpl["Brix"]
    ok = brix_min <= brix_val <= brix_max
    results.append(("Brix", f"{brix_val:.2f}", f"{brix_min}~{brix_max}", "PASS" if ok else "FAIL"))

    acid_val = float(tr["산도기여"])
    acid_min, acid_max, _ = tmpl["산도(%)"]
    ok = acid_min <= acid_val <= acid_max
    results.append(("산도(%)", f"{acid_val:.4f}", f"{acid_min}~{acid_max}", "PASS" if ok else "FAIL"))

    return results


# ──────────────────────────────────────────────
# UI 시작
# ──────────────────────────────────────────────
st.title("🧪 AI 음료 신제품 배합비 개발 플랫폼")

# ── Sidebar ──
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("OpenAI API Key", type="password", help="gpt-4o-mini 사용")

    st.divider()
    st.subheader("1️⃣ 음료 유형 선택")
    beverage_type = st.selectbox("음료 유형", list(STANDARD_TEMPLATES.keys()))

    st.subheader("2️⃣ Flavor 선택")
    flavors = TREND_FLAVORS.get(beverage_type, TREND_FLAVORS["기타음료"])
    selected_flavor = st.selectbox("트렌드 Flavor", flavors)

    st.divider()
    st.subheader("3️⃣ 목표 물성 설정")
    tmpl = STANDARD_TEMPLATES[beverage_type]
    st.caption(f"📋 {beverage_type} 표준 범위 참고:")

    target_brix = st.slider(
        f"Target Brix (표준: {tmpl['Brix'][0]}~{tmpl['Brix'][1]})",
        min_value=1.0, max_value=20.0,
        value=float(tmpl["Brix"][2]), step=0.5,
    )
    target_acid = st.slider(
        f"Target 산도% (표준: {tmpl['산도(%)'][0]}~{tmpl['산도(%)'][1]})",
        min_value=0.01, max_value=1.0,
        value=float(tmpl["산도(%)"][2]), step=0.01,
    )
    target_sweet = st.slider(
        f"Target 감미도 (표준: {tmpl['감미도'][0]}~{tmpl['감미도'][1]})",
        min_value=0.1, max_value=5.0,
        value=float(tmpl["감미도"][2]), step=0.1,
    )

# ── Main Area ──
# ── Step A: 표준 배합비 정보 표시 ──
st.header(f"📊 {beverage_type} 표준 배합비 정보")
col1, col2 = st.columns(2)

with col1:
    st.subheader("이화학 기준 범위")
    spec_data = {
        "항목": ["Brix(°)", "pH", "산도(%)", "감미도(설탕=1)"],
        "최소": [tmpl["Brix"][0], tmpl["pH"][0], tmpl["산도(%)"][0], tmpl["감미도"][0]],
        "기본값": [tmpl["Brix"][2], tmpl["pH"][2], tmpl["산도(%)"][2], tmpl["감미도"][2]],
        "최대": [tmpl["Brix"][1], tmpl["pH"][1], tmpl["산도(%)"][1], tmpl["감미도"][1]],
    }
    st.dataframe(pd.DataFrame(spec_data), hide_index=True, use_container_width=True)

with col2:
    st.subheader("원료 역할별 사용 범위")
    role_data = []
    for role, (rmin, rmax) in tmpl["roles"].items():
        role_data.append({"원료 역할": role, "최소(%)": rmin, "최대(%)": rmax})
    st.dataframe(pd.DataFrame(role_data), hide_index=True, use_container_width=True)

st.info(f"🎯 현재 목표: Brix={target_brix} | 산도={target_acid}% | 감미도={target_sweet} | Flavor: {selected_flavor}")

st.divider()

# ── Step B: 원료 DB 생성 ──
st.header("🗃️ 원료 데이터베이스")

col_db1, col_db2 = st.columns(2)
with col_db1:
    btn_api_db = st.button("🤖 AI 원료 DB 생성 (API)", use_container_width=True)
with col_db2:
    btn_builtin_db = st.button("📦 내장 원료 DB 사용", use_container_width=True)

if btn_api_db:
    client = get_openai_client(api_key)
    if client is None:
        st.error("유효한 API Key를 입력해주세요.")
    else:
        with st.spinner("ChatGPT로 원료 DB 생성 중..."):
            db = generate_ingredient_db_via_api(client, beverage_type, selected_flavor)
        if db is not None and len(db) > 0:
            st.session_state.ingredient_db = db
            st.success(f"✅ 원료 DB 생성 완료: {len(db)}종")
        else:
            st.warning("API 생성 실패 → 내장 DB를 사용합니다.")
            st.session_state.ingredient_db = get_builtin_ingredient_db(beverage_type, selected_flavor)

if btn_builtin_db:
    st.session_state.ingredient_db = get_builtin_ingredient_db(beverage_type, selected_flavor)
    st.success(f"✅ 내장 원료 DB 로드: {len(st.session_state.ingredient_db)}종")

if st.session_state.ingredient_db is not None:
    st.dataframe(st.session_state.ingredient_db, hide_index=True, use_container_width=True)

st.divider()

# ── Step C: 배합비 생성 ──
st.header("🧬 AI 배합비 생성")

if st.button("🚀 배합비 생성 (500회 시뮬레이션)", use_container_width=True):
    if st.session_state.ingredient_db is None:
        st.error("원료 DB를 먼저 생성해주세요.")
    else:
        with st.spinner("배합비 최적화 중... (500회 시뮬레이션)"):
            formula = generate_formula(
                st.session_state.ingredient_db,
                target_brix, target_acid, target_sweet,
                beverage_type,
            )
        if formula is not None:
            st.session_state.formula_result = formula
            st.success("✅ 배합비 생성 완료")
        else:
            st.error("배합비 생성 실패. 원료 DB를 확인해주세요.")

if st.session_state.formula_result is not None:
    formula = st.session_state.formula_result

    st.subheader(f"📋 {selected_flavor} — R&D 배합표")
    st.dataframe(
        formula.style.format({
            "사용량(%)": "{:.4f}",
            "Brix기여": "{:.4f}",
            "산도기여": "{:.4f}",
            "감미도기여": "{:.4f}",
            "원가기여(원/kg)": "{:.2f}",
        }),
        hide_index=True,
        use_container_width=True,
    )

    # 검증
    st.subheader("✅ 표준배합 검증")
    checks = validate_formula(formula, beverage_type)
    if checks:
        check_df = pd.DataFrame(checks, columns=["항목", "계산값", "기준범위", "판정"])
        st.dataframe(check_df, hide_index=True, use_container_width=True)

    # 엑셀 다운로드
    buffer = io.BytesIO()
    formula.to_excel(buffer, index=False, sheet_name="배합표")
    buffer.seek(0)
    st.download_button(
        "📥 엑셀 배합표 다운로드",
        data=buffer,
        file_name=f"AI_Formula_{selected_flavor.replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.divider()

    # ── Step D: AI 연구원 평가 ──
    st.header("🔬 AI 연구원 평가")

    if st.button("🧑‍🔬 AI R&D 평가 요청", use_container_width=True):
        client = get_openai_client(api_key)
        if client is None:
            st.warning("API Key가 없으므로 간이 평가를 수행합니다.")
            total_row = formula[formula["원료명"] == "■ TOTAL"]
            if not total_row.empty:
                tr = total_row.iloc[0]
                evaluation = f"""
**[간이 자동 평가]**

- **Brix**: {tr['Brix기여']:.2f}° — {'적정 범위' if tmpl['Brix'][0] <= tr['Brix기여'] <= tmpl['Brix'][1] else '범위 이탈 주의'}
- **산도**: {tr['산도기여']:.4f}% — {'적정' if tmpl['산도(%)'][0] <= tr['산도기여'] <= tmpl['산도(%)'][1] else '조정 필요'}
- **총 원가**: {tr['원가기여(원/kg)']:.0f} 원/kg

> API Key를 입력하면 ChatGPT 기반 상세 기술 평가를 받을 수 있습니다.
"""
                st.session_state.ai_evaluation = evaluation
        else:
            # 배합표를 텍스트로 변환
            formula_text = formula.to_string(index=False)
            eval_prompt = f"""
당신은 음료 R&D 연구원(식품기술사, 경력 20년)입니다.
아래 AI가 생성한 음료 배합표를 평가해주세요.

[제품 정보]
음료 유형: {beverage_type}
Flavor: {selected_flavor}
목표 Brix: {target_brix}, 목표 산도: {target_acid}%, 목표 감미도: {target_sweet}

[배합표]
{formula_text}

다음 항목을 한국어로 평가해주세요:
1. 풍미 밸런스 평가 (Flavor balance)
2. 감미 밸런스 평가 (당류 vs 감미료 비율)
3. 산도 밸런스 평가 (산미료 종류 및 양)
4. 물성/식감 평가 (Mouthfeel)
5. 기술적 개선 제안 3가지 이상
6. 원가 최적화 방안
"""
            with st.spinner("AI 연구원이 배합비를 분석 중..."):
                result = call_openai_text(
                    client,
                    "당신은 20년 경력의 음료 R&D 연구원(식품기술사)입니다. 전문적이고 실무적인 평가를 한국어로 제공하세요.",
                    eval_prompt,
                )
                st.session_state.ai_evaluation = result

    if st.session_state.ai_evaluation:
        st.markdown(st.session_state.ai_evaluation)
