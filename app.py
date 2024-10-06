import streamlit as st
from src.streamlit.data_input import streamlit_dataset_upload
import streamlit as st
import argparse


argparser = argparse.ArgumentParser()
argparser.add_argument("--data_path", type=str, default="data/nutrition_data.csv")
args = argparser.parse_args()

page_title = "Mathematically Optimal Mealplan"
page_icon = "🥗"


st.set_page_config(
    page_title=page_title,
    page_icon=page_icon,
    layout="wide",
    initial_sidebar_state="expanded",
)


st.title(f"{page_icon} Welcome To: {page_title}")
streamlit_dataset_upload(default_data_path=args.data_path)

df = st.session_state["data"]
