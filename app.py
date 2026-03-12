import streamlit as st
import pandas as pd
import numpy as np
import random

st.title("AI Beverage Formula Generator")

ingredient_db = st.file_uploader("Ingredient DB Upload (CSV)")
flavor_db = st.file_uploader("Flavor Map Upload (CSV)")

beverage_type = st.selectbox(
"Select Beverage Type",
["Carbonated","Sports","Juice"]
)

flavor = st.text_input("Flavor Name")

target_brix = st.slider("Target Brix",5.0,15.0,11.0)
target_acid = st.slider("Target Acid",0.1,1.5,0.5)

if st.button("Generate Formula"):

    ing = pd.read_csv(ingredient_db)
    fmap = pd.read_csv(flavor_db)

    subset = fmap[fmap["Flavor_Name"]==flavor]

    result = []

    for i,row in subset.iterrows():

        usage = random.uniform(row["Min_%"],row["Max_%"])

        name = row["Ingredient"]

        prop = ing[ing["Ingredient"]==name]

        if len(prop)>0:
            brix = prop["Brix"].values[0]*usage/100
            acid = prop["Acidity"].values[0]*usage/100
            cost = prop["Cost"].values[0]*usage/100
        else:
            brix=0
            acid=0
            cost=0

        result.append([
            name,
            round(usage,2),
            round(brix,2),
            round(acid,2),
            round(cost,2)
        ])

    df = pd.DataFrame(result,
        columns=["Ingredient","Usage %","Brix Contribution","Acid Contribution","Cost Contribution"]
    )

    st.subheader("Generated Formula")

    st.dataframe(df)

    st.subheader("Total")

    total=df.sum(numeric_only=True)

    st.write(total)
