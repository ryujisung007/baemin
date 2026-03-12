```python
import streamlit as st
import pandas as pd
import random
from openai import OpenAI

# -------------------------------
# API 설정
# -------------------------------
client = OpenAI(api_key="YOUR_API_KEY")

st.set_page_config(page_title="AI Beverage R&D Platform", layout="wide")

st.title("AI Beverage Development Platform")

# -------------------------------
# AI Ingredient DB 생성
# -------------------------------

def generate_ingredient_db():

    prompt = """
Create a beverage ingredient database.

Return JSON array with fields:

Ingredient
Category
Brix
pH
Acidity
Sweetness
Cost

Create about 50 ingredients.
"""

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role":"system","content":"You are a beverage R&D scientist"},
            {"role":"user","content":prompt}
        ]
    )

    text = response.choices[0].message.content

    try:
        data = pd.read_json(text)
    except:
        data = pd.DataFrame()

    return data


# -------------------------------
# 세션 DB 생성
# -------------------------------

if "ingredient_db" not in st.session_state:
    st.session_state.ingredient_db = pd.DataFrame()

# -------------------------------
# 사이드바
# -------------------------------

st.sidebar.header("AI Database")

if st.sidebar.button("Generate Ingredient DB (AI)"):

    db = generate_ingredient_db()

    st.session_state.ingredient_db = db


# -------------------------------
# DB 화면
# -------------------------------

st.header("Ingredient Database")

if len(st.session_state.ingredient_db) > 0:

    st.dataframe(st.session_state.ingredient_db)

else:

    st.info("DB not created yet")


# -------------------------------
# 음료 개발 영역
# -------------------------------

st.header("Beverage Development")

beverage_type = st.selectbox(
"Select Beverage Type",
["Carbonated","Juice","Sports Drink","Energy Drink"]
)

flavor = st.text_input("Flavor")

target_brix = st.slider("Target Brix",5.0,15.0,11.0)

target_acid = st.slider("Target Acidity",0.1,1.5,0.5)

# -------------------------------
# 레시피 생성
# -------------------------------

def generate_recipe(db):

    ingredients = db.sample(4)

    recipe=[]

    total=0

    for i,row in ingredients.iterrows():

        usage=random.uniform(0.1,5)

        recipe.append([
            row["Ingredient"],
            round(usage,2)
        ])

        total+=usage

    water=100-total

    recipe.append(["Water",round(water,2)])

    return recipe


# -------------------------------
# AI 레시피 생성
# -------------------------------

if st.button("Generate AI Rec
```
