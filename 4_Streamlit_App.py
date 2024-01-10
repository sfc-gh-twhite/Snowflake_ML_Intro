# Copy and paste this app into an SiS app
# Import python packages
from snowflake.snowpark.context import get_active_session
from snowflake.ml.utils.connection_params import SnowflakeLoginOptions
from snowflake.snowpark import Session
import base64
import pandas as pd
import streamlit as st
import sys

st.set_page_config(layout="wide")

# Get the current credentials, locally or in SiS
if sys._xoptions["snowflake_import_directory"]:
    session = get_active_session()
else:
    session = Session.builder.configs(SnowflakeLoginOptions()).getOrCreate()

st.title("Will you survive the titanic?")


@st.cache_resource
def load_images():
    sink_bytes_object = session.file.get_stream(
        "@ML_DATA/sinking.webp.gz", decompress=True
    ).read()
    sink_image64 = base64.b64encode(sink_bytes_object).decode()

    float_bytes_object = session.file.get_stream(
        "@ML_DATA/floating.webp.gz", decompress=True
    ).read()
    float_image64 = base64.b64encode(float_bytes_object).decode()

    flying_bytes_object = session.file.get_stream(
        "@ML_DATA/flying.webp.gz", decompress=True
    ).read()
    flying_image64 = base64.b64encode(flying_bytes_object).decode()

    return dict(sink=sink_image64, float=float_image64, fly=flying_image64)


@st.cache_data
def load_data(df):
    test_2 = session.table(df).to_pandas()
    return test_2


test_2 = load_data("test_data")


col1, col2, col3 = st.columns(3)

with col1:
    pclass = st.selectbox("What class is your ticket?", ["FIRST", "SECOND", "THIRD"])
    town = st.selectbox(
        "What town did you embark from?", ["SOUTHAMPTON", "CHERBOURG", "QUEENSTOWN"]
    )

with col2:
    fare = st.number_input(
        "What was the cost of your ticket?",
        min_value=0.00,
        max_value=512.00,
        value=50.00,
    )
    who = st.selectbox("Are you a Man, Woman, or Child?", ("MAN", "WOMAN", "CHILD"))
with col3:
    sibsp = st.number_input(
        "How many siblings/spouses are traveling with you?",
        min_value=0,
        max_value=8,
        value=0,
        step=1,
    )
    parch = st.number_input(
        "How many parents/children are traveling with you?",
        min_value=0,
        max_value=6,
        value=0,
        step=1,
    )


data = [[sibsp, parch, pclass, who, town, fare]]

columns = ["SIBSP", "PARCH", "CLASS", "WHO", "EMBARK_TOWN", "FARE"]

titanic_df = pd.DataFrame(data, columns=columns)

cat_cols = ["CLASS", "WHO", "EMBARK_TOWN"]
num_cols = ["SIBSP", "PARCH", "FARE"]


titanic_df = pd.get_dummies(data=titanic_df, columns=cat_cols)


# Get columns in df1 that are not in df2
new_columns = list(set(test_2.columns) - set(titanic_df.columns))

# Add missing columns to df2 and fill them with zeros
for col in new_columns:
    titanic_df[col] = 0

CLASS_SECOND = titanic_df["CLASS_SECOND"][0]
CLASS_THIRD = titanic_df["CLASS_THIRD"][0]
WHO_MAN = titanic_df["WHO_MAN"][0]
WHO_WOMAN = titanic_df["WHO_WOMAN"][0]
EMBARK_TOWN_QUEENSTOWN = titanic_df["EMBARK_TOWN_QUEENSTOWN"][0]
EMBARK_TOWN_SOUTHAMPTON = titanic_df["EMBARK_TOWN_SOUTHAMPTON"][0]
SIBSP = titanic_df["SIBSP"][0]
PARCH = titanic_df["PARCH"][0]
FARE = titanic_df["FARE"][0]

surv_pred = session.sql(
    f"""
select
survival_pred_proba(object_construct(
'CLASS_SECOND', {CLASS_SECOND},
'CLASS_THIRD', {CLASS_THIRD},
'WHO_MAN', {WHO_MAN},
'WHO_WOMAN', {WHO_WOMAN},
'EMBARK_TOWN_QUEENSTOWN', {EMBARK_TOWN_QUEENSTOWN},
'EMBARK_TOWN_SOUTHAMPTON', {EMBARK_TOWN_SOUTHAMPTON},
'SIBSP', {SIBSP},
'PARCH', {PARCH},
'FARE', {FARE}
)):output_feature_1 AS surv_prob
"""
).collect()

surv_pred = round(float(surv_pred[0][0]) * 100, 2)

st.metric(value=f"{surv_pred}%", label="Chance of surviving the Titanic")

images = load_images()

if surv_pred > 75:
    st.image(f'data:image/gif;base64,{images.get("fly")}')
    st.write("Have fun!")
elif surv_pred >= 40:
    st.image(f'data:image/gif;base64,{images.get("float")}')
    st.write("You may survive but you are going to be cold ")
else:
    st.image(f'data:image/gif;base64,{images.get("sink")}')
    st.write("I would NOT get on this boat")
