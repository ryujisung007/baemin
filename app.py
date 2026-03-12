import streamlit as st
import pandas as pd
import json
import random
import re
from openai import OpenAI

st.set_page_config(page_title="AI Beverage R&D", layout="wide")

st.title("AI Beverage Development Platform")

# -----------------------------
# API KEY 입력
# -----------------------------

st.sidebar.header("OpenAI API")

api_key = st.sidebar.text_input("Enter API Key", type="password")

client = None

if api_key:
    try:
        client = OpenAI(api_key=api_key)
        st.sidebar.success("API Connected")
    except:
        st.sidebar.error("API Error")

# -----------------------------
# JSON 추출 함수 (안정)
# -----------------------------

def extract_json(text):

    match = re.search(r"\[.*\]", text, re.S)

    if match:
        return json.loads(match.group())

    return None

# -----------------------------
# 원료 DB 생성
# -----------------------------

def generate_ingredient_db():

    if client is None:
        st.warning("API key required")
        return pd.DataFrame()

    prompt = """
Create beverage ingredient database.

Return ONLY JSON.

Format:

[
 {"Ingredient":"Sucrose","Category":"Sugar","Brix":100,"pH":7,"Acidity":0.0,"Sweetness":1.0,"Cost":1200}
]

Create 25 ingredients.

Only JSON.
"""

    try:

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role":"system","content":"You are a beverage R&D scientist"},
                {"role":"user","content":prompt}
            ]
        )

        text = response.choices[0].message.content

        data = extract_json(text)

        if data is None:
            st.error("JSON parse failed")
            st.write(text)
            return pd.DataFrame()

        df = pd.DataFrame(data)

        return df

    except Exception as e:

        st.error("API request failed")
        st.write(e)

        return pd.DataFrame()

# -----------------------------
# 레시피 생성
# -----------------------------

def generate_recipe(db):

    ingredients = db.sample(4)

    recipe=[]

    total=0

    for i,row in ingredients.iterrows():

        usage=round(random.uniform(0.1,5),2)

        recipe.append({
            "Ingredient":row["Ingredient"],
            "Usage %":usage,
            "Brix":row["Brix"],
            "pH":row["pH"],
            "Cost":row["Cost"]
        })

        total+=usage

    water=round(100-total,2)

    recipe.append({
        "Ingredient":"Water",
        "Usage %":water,
        "Brix":0,
        "pH":7,
        "Cost":0
    })

    return pd.DataFrame(recipe)

# -----------------------------
# session
# -----------------------------

if "ingredient_db" not in st.session_state:
    st.session_state.ingredient_db = pd.DataFrame()

# -----------------------------
# DB 생성 버튼
# -----------------------------

st.sidebar.header("Ingredient DB")

if st.sidebar.button("Generate Ingredient DB"):

    df=generate_ingredient_db()

    if len(df)>0:

        st.session_state.ingredient_db=df

# -----------------------------
# DB 출력
# -----------------------------

st.header("Ingredient Database")

if len(st.session_state.ingredient_db)>0:

    st.dataframe(st.session_state.ingredient_db)

else:

    st.info("Generate Ingredient DB first")

# -----------------------------
# 음료 생성
# -----------------------------

st.header("Beverage Development")

beverage_type=st.selectbox(
"Beverage Type",
[
"Carbonated Drink",
"Fruit Juice",
"Sports Drink",
"Energy Drink",
"Functional Beverage"
]
)

flavor=st.text_input("Flavor")

if st.button("Generate Recipe"):

    db=st.session_state.ingredient_db

    if len(db)==0:

        st.warning("Ingredient DB required")

    else:

        recipe=generate_recipe(db)

        st.subheader("Formula Sheet")

        st.dataframe(recipe)

        st.write("Total Usage %:",recipe["Usage %"].sum())
