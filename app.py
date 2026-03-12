import streamlit as st
import pandas as pd
import numpy as np
import random
import json
import re
from openai import OpenAI

st.set_page_config(page_title="AI Beverage R&D Platform", layout="wide")

st.title("AI Beverage Development Platform")

# ---------------------------

# API KEY 입력

# ---------------------------

st.sidebar.header("OpenAI API")

api_key = st.sidebar.text_input("Enter API Key", type="password")

client = None

if api_key:
try:
client = OpenAI(api_key=api_key)
st.sidebar.success("API Connected")
except:
st.sidebar.error("API Error")

# ---------------------------

# JSON 안전 파싱 (디버그1)

# ---------------------------

def safe_json(text):

```
try:
    return json.loads(text)
except:
    match = re.search(r'\{.*\}', text, re.S)
    if match:
        return json.loads(match.group())
    return None
```

# ---------------------------

# 트렌드 제품 생성

# ---------------------------

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

df = pd.DataFrame(products, columns=["Product","Flavor"])

return df
```

# ---------------------------

# 원료 DB 생성

# ---------------------------

def generate_ingredient_db(flavor):

```
ingredients = []

sugars = ["Sucrose","Fructose","Glucose","HFCS","Erythritol","Allulose"]
acids = ["Citric Acid","Malic Acid","Tartaric Acid"]
extracts = [f"{flavor} Extract",f"{flavor} Concentrate"]
stabilizers = ["Pectin","CMC","Xanthan Gum"]
colors = ["Beta Carotene","Caramel Color","Anthocyanin"]

for i in range(500):

    name = random.choice(
        sugars + acids + extracts + stabilizers + colors
    ) + f"_{i}"

    category = random.choice(
        ["Sugar","Acid","Extract","Stabilizer","Color","Flavor"]
    )

    ingredient = {
        "Ingredient":name,
        "Category":category,
        "Flavor":flavor,
        "Brix":round(random.uniform(0,100),2),
        "Acid":round(random.uniform(0,6),3),
        "Sweetness":round(random.uniform(0,200),2),
        "Cost":round(random.uniform(500,9000),2),
        "Purpose":random.choice(
            ["Sweetener","Acidity","Flavor","Stabilizer","Color"]
        ),
        "FlavorContribution":random.choice(
            ["Sweet","Sour","Citrus","Berry","Neutral"]
        )
    }

    ingredients.append(ingredient)

return pd.DataFrame(ingredients)
```

# ---------------------------

# 배합 생성

# ---------------------------

def generate_formula(db, target_brix, target_sweet, target_acid):

```
best_score = 999999
best_formula = None

for _ in range(1000):

    sample = db.sample(6)

    usages = np.random.rand(6)

    usages = usages / usages.sum() * 100

    formula = sample.copy()

    formula["Usage"] = usages

    total_brix = np.sum(formula["Usage"] * formula["Brix"] / 100)
    total_sweet = np.sum(formula["Usage"] * formula["Sweetness"] / 100)
    total_acid = np.sum(formula["Usage"] * formula["Acid"] / 100)

    score = abs(target_brix-total_brix) + \
            abs(target_sweet-total_sweet) + \
            abs(target_acid-total_acid)

    if score < best_score:

        best_score = score
        best_formula = formula

return best_formula
```

# ---------------------------

# 표준 배합 검증

# ---------------------------

def validate_formula(df):

```
brix = np.sum(df["Usage"] * df["Brix"] / 100)
acid = np.sum(df["Usage"] * df["Acid"] / 100)

result = "PASS"

if not (6 <= brix <= 14):
    result = "FAIL"

if not (0.1 <= acid <= 0.35):
    result = "FAIL"

return brix, acid, result
```

# ---------------------------

# AI 연구원 평가

# ---------------------------

def ai_evaluate(df):

```
if client is None:
    return "API key required"

table = df.to_string()

prompt = f"""
```

Evaluate beverage formulation.

Formula:

{table}

Provide R&D evaluation and improvement suggestions.
"""

```
try:

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role":"user","content":prompt}]
    )

    return response.choices[0].message.content

except:

    return "AI evaluation failed"
```

# ---------------------------

# UI

# ---------------------------

st.header("1. Trend Products")

products = generate_trend_products()

st.dataframe(products)

selected = st.selectbox(
"Select Product",
products["Product"]
)

flavor = products.loc[
products["Product"]==selected,"Flavor"
].values[0]

# ---------------------------

# 목표 물성

# ---------------------------

st.header("2. Target Properties")

target_brix = st.slider("Target Brix",4,14,10)
target_sweet = st.slider("Target Sweetness",1,10,7)
target_acid = st.slider("Target Acid",0.05,0.5,0.2)

# ---------------------------

# 원료 DB 생성

# ---------------------------

st.header("3. Generate Ingredient DB")

if st.button("Generate Ingredient DB (500)"):

```
db = generate_ingredient_db(flavor)

st.session_state["db"] = db

st.success("Ingredient DB Generated")
```

if "db" in st.session_state:

```
st.dataframe(st.session_state["db"].head(20))
```

# ---------------------------

# 배합 생성

# ---------------------------

st.header("4. Generate Formula")

if st.button("Generate Formula"):

```
db = st.session_state["db"]

formula = generate_formula(db,target_brix,target_sweet,target_acid)

st.session_state["formula"] = formula

st.dataframe(formula)
```

# ---------------------------

# 검증

# ---------------------------

if "formula" in st.session_state:

```
st.header("5. Formula Validation")

brix, acid, result = validate_formula(st.session_state["formula"])

st.write("Brix:",round(brix,2))
st.write("Acid:",round(acid,3))
st.write("Result:",result)
```

# ---------------------------

# AI 평가

# ---------------------------

if "formula" in st.session_state:

```
st.header("6. AI R&D Evaluation")

if st.button("Evaluate Formula"):

    evaluation = ai_evaluate(st.session_state["formula"])

    st.write(evaluation)
```
