import streamlit as st
import pandas as pd
import numpy as np
import random
import math
import io
from openai import OpenAI
from scipy.optimize import minimize

st.set_page_config(page_title="AI 음료 개발 플랫폼", layout="wide")

st.title("AI 음료 개발 플랫폼 (AI Beverage R&D Engine)")

# -------------------------------------------------
# OpenAI API
# -------------------------------------------------

st.sidebar.header("OpenAI API 설정")

api_key = st.sidebar.text_input("API KEY 입력", type="password")

client = None

if api_key:
    try:
        client = OpenAI(api_key=api_key)
        st.sidebar.success("API 연결 완료")
    except:
        st.sidebar.error("API 연결 실패")

# -------------------------------------------------
# 트렌드 제품
# -------------------------------------------------

def trend_products():

    products=[
        ("Yuzu Spark Energy","유자"),
        ("Peach Ice Booster","복숭아"),
        ("Calamansi Charge","깔라만시"),
        ("Lychee Fresh Drop","리치"),
        ("Mango Power Burst","망고"),
        ("Pineapple Active","파인애플"),
        ("Grapefruit Revive","자몽"),
        ("Blueberry Pulse","블루베리"),
        ("Green Apple Spark","청사과"),
        ("Passion Energy","패션후르츠"),
        ("Cherry Vital","체리"),
        ("Watermelon Chill","수박"),
        ("Guava Booster","구아바"),
        ("Lemon Lime Rush","레몬라임"),
        ("Dragonfruit Spark","용과"),
        ("Coconut Active","코코넛"),
        ("Tropical Mix Burst","트로피컬"),
        ("Berry Mix Boost","베리믹스"),
        ("Honey Citrus Flow","허니시트러스"),
        ("Melon Fresh Pulse","멜론")
    ]

    return pd.DataFrame(products, columns=["제품명","Flavor"])

products = trend_products()

st.header("1️⃣ 트렌드 음료 선택")

cols = st.columns(4)

for i,row in products.iterrows():

    with cols[i % 4]:

        if st.button(row["제품명"]):

            st.session_state["selected_product"] = row["제품명"]
            st.session_state["selected_flavor"] = row["Flavor"]

if "selected_product" not in st.session_state:

    st.warning("트렌드 음료를 먼저 선택하세요")

    st.stop()

st.success(f"선택된 제품 : {st.session_state['selected_product']}")

flavor = st.session_state["selected_flavor"]

# -------------------------------------------------
# 목표 물성
# -------------------------------------------------

st.header("2️⃣ 목표 물성 설정")

col1,col2,col3 = st.columns(3)

with col1:
    target_brix = st.slider("목표 당도 (Brix)",4,14,10)

with col2:
    target_sweet = st.slider("목표 감미도",1,15,7)

with col3:
    target_acid = st.slider("목표 산도",0.05,0.5,0.2)

# -------------------------------------------------
# 원료 DB 생성
# -------------------------------------------------

def generate_ingredient_db(flavor):

    ingredients=[]

    sugars=["Sucrose","Fructose","Glucose","HFCS","Allulose"]
    acids=["Citric Acid","Malic Acid","Lactic Acid"]
    extracts=[f"{flavor} Extract",f"{flavor} Concentrate"]
    stabilizers=["Pectin","CMC","Xanthan"]

    for i in range(500):

        cat=random.choice(["Sugar","Acid","Extract","Stabilizer"])

        if cat=="Sugar":
            name=random.choice(sugars)
        elif cat=="Acid":
            name=random.choice(acids)
        elif cat=="Extract":
            name=random.choice(extracts)
        else:
            name=random.choice(stabilizers)

        ingredient={
            "Ingredient":f"{name}_{i}",
            "Category":cat,
            "Brix":round(random.uniform(0,100),2),
            "Sweetness":round(random.uniform(0,200),2),
            "Acid":round(random.uniform(0,6),3),
            "Cost":round(random.uniform(500,9000),2)
        }

        ingredients.append(ingredient)

    return pd.DataFrame(ingredients)

st.header("3️⃣ 원료 데이터 생성")

if st.button("원료 DB 500개 생성"):

    db = generate_ingredient_db(flavor)

    st.session_state["db"] = db

    st.success("원료 데이터 생성 완료")

if "db" not in st.session_state:
    st.stop()

st.dataframe(st.session_state["db"].head(20))

# -------------------------------------------------
# 배합 Solver
# -------------------------------------------------

def optimize_formula(db,target_brix,target_sweet,target_acid):

    sugar=db[db.Category=="Sugar"].sample(1).iloc[0]
    acid=db[db.Category=="Acid"].sample(1).iloc[0]
    flavor=db[db.Category=="Extract"].sample(1).iloc[0]
    stabilizer=db[db.Category=="Stabilizer"].sample(1).iloc[0]

    ingredients=[sugar,acid,flavor,stabilizer]

    def objective(x):

        brix=np.sum(x*[i.Brix for i in ingredients])/100
        sweet=np.sum(x*[i.Sweetness for i in ingredients])/100
        acid_val=np.sum(x*[i.Acid for i in ingredients])/100

        error=(brix-target_brix)**2 + (sweet-target_sweet)**2 + (acid_val-target_acid)**2

        return error

    x0=[6,0.2,1.2,0.1]

    bounds=[(3,12),(0.1,0.5),(0.5,3),(0.05,0.3)]

    result=minimize(objective,x0,bounds=bounds)

    sugar_u,acid_u,flavor_u,stab_u=result.x

    water=100-(sugar_u+acid_u+flavor_u+stab_u)

    formula=pd.DataFrame({
        "원료":["Water",sugar.Ingredient,acid.Ingredient,flavor.Ingredient,stabilizer.Ingredient],
        "사용량(%)":[water,sugar_u,acid_u,flavor_u,stab_u]
    })

    return formula

# -------------------------------------------------
# 배합 계산
# -------------------------------------------------

st.header("4️⃣ AI 배합 계산")

if st.button("배합 계산 실행"):

    formula=optimize_formula(st.session_state.db,target_brix,target_sweet,target_acid)

    st.session_state["formula"]=formula

    st.dataframe(formula)

# -------------------------------------------------
# 물성 계산
# -------------------------------------------------

def calculate_properties(formula,db):

    brix=0
    acid=0

    for _,row in formula.iterrows():

        name=row["원료"]

        data=db[db.Ingredient==name]

        if len(data)>0:

            brix+=row["사용량(%)"]*data.iloc[0].Brix/100
            acid+=row["사용량(%)"]*data.iloc[0].Acid/100

    ph=3-math.log10(acid+0.0001)

    return round(brix,2),round(acid,3),round(ph,2)

if "formula" in st.session_state:

    st.header("5️⃣ 배합 물성 계산")

    brix,acid,ph=calculate_properties(st.session_state.formula,st.session_state.db)

    st.write("계산 Brix:",brix)
    st.write("계산 산도:",acid)
    st.write("예측 pH:",ph)

# -------------------------------------------------
# Excel Export
# -------------------------------------------------

if "formula" in st.session_state:

    buffer=io.BytesIO()

    with pd.ExcelWriter(buffer,engine="xlsxwriter") as writer:

        st.session_state.formula.to_excel(writer,index=False)

    st.download_button(
        "배합표 Excel 다운로드",
        buffer.getvalue(),
        "beverage_formula.xlsx",
        "application/vnd.ms-excel"
    )

# -------------------------------------------------
# AI 연구원 평가
# -------------------------------------------------

if "formula" in st.session_state and client:

    st.header("6️⃣ AI 연구원 평가")

    if st.button("AI 배합 평가 실행"):

        table=st.session_state.formula.to_string()

        prompt=f"""
당신은 글로벌 음료회사 수석 연구원입니다.

다음 배합을 기술적으로 평가하세요.

{table}

다음 항목을 분석하세요

1 맛 밸런스
2 감미 구조
3 산미 균형
4 기술 개선 제안
5 상업화 가능성
"""

        response=client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role":"user","content":prompt}]
        )

        st.write(response.choices[0].message.content)
