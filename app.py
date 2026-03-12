import streamlit as st
import pandas as pd
import numpy as np
import random

st.set_page_config(page_title="AI Beverage Developer",layout="wide")

st.title("AI Beverage Development Platform")

st.sidebar.header("Target Beverage Setting")

target_brix = st.sidebar.slider("Target Brix",5.0,15.0,11.0)
target_ph = st.sidebar.slider("Target pH",2.5,5.0,3.4)
target_acid = st.sidebar.slider("Target Acidity",0.1,1.5,0.5)
target_sweet = st.sidebar.slider("Target Sweetness",0.5,2.0,1.0)

uploaded_file = st.file_uploader("Upload Ingredient DB (CSV)")

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.subheader("Ingredient Database")
    st.dataframe(df)

    recipes = []

    for i in range(1000):

        sample = df.sample(6)

        usage = np.random.dirichlet(np.ones(6))*100

        brix = np.sum(sample["Brix"].values * usage)/100

        ph_effect = np.sum(sample["pH"].values * usage)/100

        acid = np.sum(sample["Acidity"].values * usage)/100

        sweetness = 0
        if "Sweetness" in df.columns:
            sweetness = np.sum(sample["Sweetness"].values * usage)/100

        cost = 0
        if "Cost" in df.columns:
            cost = np.sum(sample["Cost"].values * usage)/100

        score = (
        abs(target_brix-brix)*30 +
        abs(target_ph-ph_effect)*25 +
        abs(target_acid-acid)*25 +
        abs(target_sweet-sweetness)*20
        )

        recipes.append([
        i,
        round(brix,2),
        round(ph_effect,2),
        round(acid,2),
        round(sweetness,2),
        round(cost,2),
        round(score,2)
        ])

    result = pd.DataFrame(recipes,columns=[
    "RecipeID",
    "Brix",
    "pH",
    "Acidity",
    "Sweetness",
    "Cost",
    "Score"
    ])

    best = result.sort_values("Score").head(20)

    st.subheader("Top AI Generated Recipes")

    st.dataframe(best)

    st.subheader("Score Distribution")

    st.bar_chart(best["Score"])

    st.subheader("Brix Distribution")

    st.bar_chart(best["Brix"])

    st.subheader("Acidity Distribution")

    st.bar_chart(best["Acidity"])
