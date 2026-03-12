import streamlit as st
import pandas as pd
import random

st.title("AI 음료 개발 프로그램")

st.sidebar.header("목표 설정")

target_brix = st.sidebar.slider("Target Brix",5,15,11)
target_ph = st.sidebar.slider("Target pH",2.5,5.0,3.4)
target_acid = st.sidebar.slider("Target Acidity",0.1,1.0,0.5)

uploaded_file = st.file_uploader("원료 DB 업로드 (CSV)")

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.subheader("원료 DB")
    st.dataframe(df)

    recipes = []

    for i in range(1000):

        sample = df.sample(5)

        brix = (sample["Brix"] * random.uniform(0.1,5)).sum()
        ph = (sample["pH"] * random.uniform(0.1,1)).mean()
        acid = (sample["Acidity"] * random.uniform(0.1,1)).sum()

        score = abs(target_brix-brix)+abs(target_ph-ph)+abs(target_acid-acid)

        recipes.append([i,brix,ph,acid,score])

    result = pd.DataFrame(recipes,columns=["ID","Brix","pH","Acidity","Score"])

    best = result.sort_values("Score").head(10)

    st.subheader("추천 레시피")
    st.dataframe(best)

    st.bar_chart(best["Score"])
