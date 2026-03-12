import streamlit as st
import pandas as pd
import random
from openai import OpenAI

st.set_page_config(page_title="AI Beverage R&D Platform", layout="wide")

st.title("AI Beverage Development Platform")

# API KEY 입력
st.sidebar.header("OpenAI API")

api_key = st.sidebar.text_input("Enter OpenAI API Key", type="password")

client = None

if api_key:
    try:
        client = OpenAI(api_key=api_key)
        st.sidebar.success("API Key loaded")
    except:
        st.sidebar.error("API initialization failed")


# Ingredient DB 생성
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

Create about 20 ingredients.
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

        df = pd.read_json(text)

        return df

    except Exception as e:

        st.error("API request failed")
        st.write(e)

        return pd.DataFrame()


# session state
if "ingredient_db" not in st.session_state:
    st.session_state.ingredient_db = pd.DataFrame()


# DB 생성 버튼
if st.sidebar.button("Generate Ingredient DB"):

    db = generate_ingredient_db()

    if len(db) > 0:
        st.session_state.ingredient_db = db


# DB 출력
st.header("Ingredient Database")

if len(st.session_state.ingredient_db) > 0:
    st.dataframe(st.session_state.ingredient_db)
else:
    st.info("No database yet")


# Beverage 개발
st.header("Beverage Development")

beverage_type = st.selectbox(
"Beverage Type",
["Carbonated","Juice","Sports Drink","Energy Drink"]
)

flavor = st.text_input("Flavor")


def generate_recipe(db):

    ingredients = db.sample(min(3,len(db)))

    recipe=[]
    total=0

    for i,row in ingredients.iterrows():

        usage=random.uniform(0.1,5)

        recipe.append([row["Ingredient"],round(usage,2)])

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

        st.write("Total:",df["Usage %"].sum())
