import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import os
import streamlit as st


def display_mealplan_in_streamlit(dataframe):
    st.title("Daily Mealplan")
    top_cols = st.columns([1, 1])
    with top_cols[0]:
        cols = st.columns([1.5, 6, 1.5, 1.5])
        with cols[0]:
            st.write("**Image**")  # Title for the image column
        with cols[1]:
            st.write("**FDC Name**")  # Title for the product name column
        with cols[2]:
            st.write("**Quantity (g)**")
        with cols[3]:
            st.write("**Price (EUR)**")

        for _, row in dataframe.iterrows():
            columns = st.columns([1, 6, 1, 1])  # Adjust column widths as necessary
            with columns[0]:
                if row["Image"]:
                    st.image(row["Image"], width=60)  # Adjust width to fit the layout
                else:
                    st.write("No image available")
            with columns[1]:
                st.write(row["FDC Name"])
            with columns[2]:
                st.write(row["Optimal Quantity (g)"])
            with columns[3]:
                st.write(row["Price (EUR)"])

        st.write("Total Price (EUR): ", dataframe["Price (EUR)"].sum())


def create_shopping_list_inplace(merged_df):
    DAYS_PER_WEEK = 7

    merged_df["Shopping List.Product Name"] = merged_df["Non Nutrient Data.FDC Name"]

    merged_df["Shopping List.Average Weekly Price (EUR)"] = (
        DAYS_PER_WEEK * merged_df["Daily Mealplan.Price (EUR)"]
    )

    merged_df["Shopping List.Optimal Weekly Quantity (g)"] = (
        DAYS_PER_WEEK * merged_df["Daily Mealplan.Optimal Quantity (g)"]
    )
    merged_df["Shopping List.Product Package Weight (g)"] = (
        merged_df["Non Nutrient Data.Amount"]
        * merged_df["Non Nutrient Data.Weight per Unit (g)"]
    ).astype(int)

    merged_df["Shopping List.Product Package Quantity (units)"] = (
        merged_df["Shopping List.Optimal Weekly Quantity (g)"]
        / merged_df["Shopping List.Product Package Weight (g)"]
    )

    import math

    def calculate_packages_and_weeks(row):
        quantity = row["Shopping List.Product Package Quantity (units)"]
        if quantity >= 1:
            packages = math.ceil(quantity)
            weeks = 1
        else:
            packages = 1
            weeks = math.floor(1 / quantity)
        return pd.Series([packages, weeks])

    # Apply the function to create new columns
    merged_df[
        [
            "Shopping List.Product Package Quantity Per Period (units / week)",
            "Shopping List.Shopping Period (weeks)",
        ]
    ] = merged_df.apply(calculate_packages_and_weeks, axis=1)
    return merged_df


def create_meaplan_from_optimizer_results(
    df,
    flat_column_normalized_result_df,
    optimization_unit_size=100,
    directory="data/processed",
    file_name="merged_optimization_result.csv",
    streamlit_mealplan_columns=[
        "FDC Name",
        "Optimal Quantity (g)",
        "Price (EUR)",
        "Image",
    ],
):

    flat_column_df = df.copy()
    flat_column_df.columns = [
        ".".join(map(str, col)).strip() for col in df.columns.values
    ]

    merged_df = pd.merge(
        flat_column_normalized_result_df,
        flat_column_df,
        left_on="Non Nutrient Data.FDC Name",
        right_on="Non Nutrient Data.FDC Name",
        how="left",
        suffixes=("", "_drop"),
    )
    merged_df = merged_df.loc[:, ~merged_df.columns.str.endswith("_drop")]

    merged_df["Daily Mealplan.Optimal Quantity (g)"] = (
        optimization_unit_size * merged_df["Non Nutrient Data.Optimal Quantity"]
    )
    merged_df["Daily Mealplan.Price (EUR)"] = (
        merged_df["Non Nutrient Data.Price per 100g"]
        / 100
        * merged_df["Daily Mealplan.Optimal Quantity (g)"]
    ).round(2)

    merged_df = create_shopping_list_inplace(merged_df)

    file_path = os.path.join(directory, file_name)
    os.makedirs(directory, exist_ok=True)
    merged_df.to_csv(file_path, index=False)
    merged_df = merged_df[streamlit_mealplan_columns]

    merged_df.columns = [
        col.replace("Non Nutrient Data.", "") for col in merged_df.columns
    ]

    merged_df.columns = [
        col.replace("Daily Mealplan.", "") for col in merged_df.columns
    ]

    # Assuming 'merged_df' is your DataFrame that has already been loaded elsewhere in your script

    def load_image(url):
        try:
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            return img
        except Exception as e:
            return None  # Returns None if there's an issue loading the image

    # Convert Image URLs to actual images
    merged_df["Image"] = merged_df["Image URL"].apply(load_image)
    return merged_df
