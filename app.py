python
import streamlit as st
import pandas as pd
import random
from openai import OpenAI

st.set_page_config(page_title="AI Beverage R&D Platform", layout="wide")

st.title("AI Beverage Development Platform")

# -----------------------------
# API KEY 입력
# -----------------------------

st.sidebar.header("OpenAI API")

api_key = st.sidebar.text_input(
    "Enter OpenAI API Key",
    type="password"
)

client = None

if api_key:
    try:
        client = OpenAI(api_key=api_key)
        st.sidebar.success("API Key loaded")
    except Exception:
        st.sidebar.error("API Key initialization failed")


# -----------------------------
# Ingredient DB 생성 함수
# -----------------------------

def generate_ingredient_db():

    if client is None:
        st.warning("Enter valid API Key first")
        return pd.DataFrame()

    prompt = """
Create beverage ingredient database.

Return JSON array with fields:

Ingredient
Category
Brix
pH
Acidity
Sweetness
Cost

Create about 30 ingredients.
"""

    try:

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role":"system","content":"You are a beverage R&D scientist"},
                {"role":"user","content":prompt}
            ],
            temperature=0.2
        )

        text = response.choices[0].message.content

        df = pd.read_json(text)

        return df

    except Exception as e:

        st.error("API request failed")
        st.write(e)

        return pd.DataFrame()


# -----------------------------
# 세션 상태
# -----------------------------

if "ingredient_db" not in st.session_state:
    st.session_state.ingredient_db = pd.DataFrame()


# -----------------------------
# DB 생성 버튼
# -----------------------------

st.sidebar.header("AI Database")

if st.sidebar.button("Generate Ingredient DB"):

    if not api_key:
        st.warning("Please input API key first")

    else:

        db = generate_ingredient_db()

        if len(db) > 0:
            st.session_state.ingredient_db = db
            st.success("Ingredient DB created")


# -----------------------------
# DB 출력
# -----------------------------

st.header("Ingredient Database")

if len(st.session_state.ingredient_db) > 0:

    st.dataframe(st.session_state.ingredient_db)

else:

    st.info("No database yet")


# -----------------------------
# 음료 개발
# -----------------------------

st.header("Beverage Development")

beverage_type = st.selectbox(
"Beverage Type",
["Carbonated","Juice","Sports Drink","Energy Drink"]
)

flavor = st.text_input("Flavor")

target_brix = st.slider("Target Brix",5.0,15.0,11.0)

target_acid = st.slider("Target Acidity",0.1,1.5,0.5)


# -----------------------------
# 레시피 생성
# -----------------------------

def generate_recipe(db):

    ingredients = db.sample(min(4,len(db)))

    recipe=[]

    total=0

    for i,row in ingredients.iterrows():

        usage=random.uniform(0.1,5)

        recipe.append([
            row["Ingredient"],
            round(usage,2)
        ])

        total+=usage

    water=max(0,100-total)

    recipe.append(["Water",round(water,2)])

    return recipe


if st.button("Generate AI Recipe"):

    db=st.session_state.ingredient_db

    if len(db)==0:

        st.warning("Generate Ingredient DB first")

    else:

        recipe=generate_recipe(db)

        df=pd.DataFrame(recipe,columns=["Ingredient","Usage %"])

        st.subheader("Formula Sheet")

        st.dataframe(df)

        st.subheader("Total Usage")

        st.write(round(df["Usage %"].sum(),2))


# -----------------------------
# CSV 다운로드
# -----------------------------

if len(st.session_state.ingredient_db)>0:

    csv=st.session_state.ingredient_db.to_csv(index=False)

    st.download_button(
        label="Download Ingredient DB",
        data=csv,
        file_name="ingredient_db.csv"
    )

