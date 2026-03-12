import streamlit as st
import pandas as pd
import numpy as np
import random
from openai import OpenAI

st.set_page_config(page_title="AI Beverage R&D Platform", layout="wide")

st.title("AI Beverage Development Platform")

# -----------------------

# API KEY

# -----------------------

st.sidebar.header("OpenAI API")

api_key = st.sidebar.text_input("API KEY", type="password")

client = None

if api_key:
try:
client = OpenAI(api_key=api_key)
st.sidebar.success("Connected")
except:
st.sidebar.error("API Error")

# -----------------------

# 트렌드 제품

# -----------------------

def generate_trend_products():

```
products = [

    ("Yuzu Spark Energy","Yuzu"),
    ("Peach Ice Booster","Peach"),
    ("Calamansi Charge","Calamansi"),
    ("Lychee Fresh Drop","Lychee"),
    ("Mango Power Burst","Mango"),
    ("Pineapple Active","Pineapple"),
    ("Grapefruit Revive","Grapefruit"),
    ("Blueberry Pulse","Blueberry"),
    ("Green Apple Spark","Green Apple"),
    ("Passion Energy","Passionfruit"),
    ("Cherry Vital","Cherry"),
    ("Watermelon Chill","Watermelon"),
    ("Guava Booster","Guava"),
    ("Lemon Lime Rush","Lemon Lime"),
    ("Dragonfruit Spark","Dragonfruit"),
    ("Coconut Active","Coconut"),
    ("Tropical Mix Burst","Tropical"),
    ("Berry Mix Boost","Berry Mix"),
    ("Honey Citrus Flow","Honey Citrus"),
    ("Melon Fresh Pulse","Melon")

]

return pd.DataFrame(products, columns=["Product","Flavor"])
```

products = generate_trend_products()

st.header("1. Trend Products")

st.write("Click a product to select")

cols = st.columns(4)

for i, row in products.iterrows():

```
with cols[i % 4]:

    if st.button(row["Product"]):

        st.session_state["selected_product"] = row["Product"]
        st.session_state["selected_flavor"] = row["Flavor"]
```

# -----------------------

# 선택된 제품 표시

# -----------------------

if "selected_product" in st.session_state:

```
st.success(f"Selected Product : {st.session_state['selected_product']}")

flavor = st.session_state["selected_flavor"]
```

else:

```
st.warning("Select a product first")
st.stop()
```

# -----------------------

# 목표 물성

# -----------------------

st.header("2. Target Properties")

target_brix = st.slider("Target Brix", 4, 14, 10)

target_sweet = st.slider("Target Sweetness", 1, 10, 7)

target_acid = st.slider("Target Acid", 0.05, 0.5, 0.2)

# -----------------------

# 원료 DB 생성

# -----------------------

def generate_ingredient_db(flavor):

```
ingredients = []

for i in range(500):

    ingredient = {

        "Ingredient": f"{flavor}_ingredient_{i}",

        "Category": random.choice(
            ["Sugar","Acid","Extract","Stabilizer","Color"]
        ),

        "Brix": round(random.uniform(0,100),2),

        "Sweetness": round(random.uniform(0,200),2),

        "Acid": round(random.uniform(0,5),3),

        "Cost": round(random.uniform(500,8000),2)

    }

    ingredients.append(ingredient)

return pd.DataFrame(ingredients)
```

st.header("3. Ingredient DB")

if st.button("Generate Ingredient DB"):

```
db = generate_ingredient_db(flavor)

st.session_state["db"] = db

st.success("500 Ingredient Generated")
```

if "db" in st.session_state:

```
st.dataframe(st.session_state["db"].head(20))
```

# -----------------------

# 배합 계산

# -----------------------

def calculate_formula(db, target_brix, target_sweet, target_acid):

```
sugar = db[db["Category"]=="Sugar"].sample(1)
acid = db[db["Category"]=="Acid"].sample(1)
flavor = db[db["Category"]=="Extract"].sample(1)
stabilizer = db[db["Category"]=="Stabilizer"].sample(1)

sugar_usage = target_brix * 0.8
acid_usage = target_acid * 2

flavor_usage = random.uniform(0.8,1.5)
stabilizer_usage = random.uniform(0.05,0.2)

water_usage = 100 - (
    sugar_usage +
    acid_usage +
    flavor_usage +
    stabilizer_usage
)

formula = pd.DataFrame({

    "Ingredient":[
        "Water",
        sugar.iloc[0]["Ingredient"],
        acid.iloc[0]["Ingredient"],
        flavor.iloc[0]["Ingredient"],
        stabilizer.iloc[0]["Ingredient"]
    ],

    "Usage":[
        water_usage,
        sugar_usage,
        acid_usage,
        flavor_usage,
        stabilizer_usage
    ]

})

return formula
```

# -----------------------

# 배합 생성

# -----------------------

st.header("4. Generate Formula")

if st.button("Calculate Formula"):

```
db = st.session_state["db"]

formula = calculate_formula(db,target_brix,target_sweet,target_acid)

st.session_state["formula"] = formula

st.dataframe(formula)
```

# -----------------------

# AI 평가

# -----------------------

if "formula" in st.session_state:

```
st.header("5. AI R&D Evaluation")

if st.button("AI Evaluate"):

    table = st.session_state["formula"].to_string()

    prompt = f"""
```

You are beverage R&D scientist.

Evaluate this formulation.

{table}

Give improvement suggestions.
"""

```
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role":"user","content":prompt}]
    )

    st.write(response.choices[0].message.content)
```
