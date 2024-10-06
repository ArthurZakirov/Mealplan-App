import streamlit as st
import os
import yaml
import streamlit as st
import openpyxl
import pandas as pd
import io
import argparse
from src.visualization.dashboard import (
    create_absolute_summed_macronutrient_figure,
    create_normalized_stacked_micronutrient_figure,
    create_normalized_summed_micronutrient_figure,
    create_absolute_stacked_macronutrient_figure,
)
from src.nutrition.optimization import create_absolute_optimization_results_summary
from src.sheets.shoppinglist_spreadsheet import create_shopping_list_sheet
from src.sheets.mealplan_spreadsheet import create_mealplan_spreadsheet
from src.streamlit.page_config import set_page_config
from src.streamlit.data_input import streamlit_dataset_upload
from src.streamlit.references import display_calorie_change_studies
from src.streamlit.page_interaction import (
    user_input_energy,
    user_input_macronutrients,
    user_input_micronutrients,
    show_micronutrient_health_outcomes,
    user_input_optimization_settings,
    user_input_body_type,
    initialize_macro_rdi_session_state,
    determine_daily_calorie_change,
    manage_constraints,
    input_current_user_stats,
)
from src.streamlit.mealplan_output import (
    display_mealplan_in_streamlit,
    create_meaplan_from_optimizer_results,
)
from src.nutrition.formulas import calculate_nutrient_goals
from src.nutrition.optimization import save_optimization_results
from src.nutrition.optimization import (
    optimize_diet,
    create_normalized_optimization_results_summary,
)
from src.visualization.dashboard import visualize_optimization_result_nutrient_breakdown


parser = argparse.ArgumentParser()
parser.add_argument("--config", type=str, default="config/app_config.yaml")
parser.add_argument(
    "--spreadsheet_config", type=str, default="config/spreadsheet_config.yaml"
)
parser.add_argument(
    "--shopping_config", type=str, default="config/shopping_list_config.yaml"
)
args = parser.parse_args()


css = set_page_config()

df = st.session_state["data"]


with open(os.path.join(os.path.dirname(__file__), "..", args.config), "r") as file:
    config = yaml.safe_load(file)


if "debug" not in st.session_state:
    st.session_state["debug"] = config["debug"]

optimization_path = os.path.join(
    config["mealplan_path"], "merged_optimization_result.csv"
)


# Accessing the variables
selected_body_type = config["selected_body_type"]
show_mealplan = config["show_mealplan"]
show_micronutrient_health_outcomes_bool = config[
    "show_micronutrient_health_outcomes_bool"
]
image_path = config["image_path"]
normalized_raw_output_path = config["normalized_raw_output_path"]
absolute_raw_output_path = config["absolute_raw_output_path"]
output_path = config["output_path"]
mealplan_path = config["mealplan_path"]
upload_spreadsheet = config["upload_spreadsheet"]
upload_shopping_list = config["upload_shopping_list"]


st.markdown("### 1. Your Situation")
with st.expander("Situation"):
    if selected_body_type:
        image_dir = os.path.join(os.path.dirname(__file__), "..", image_path)
        selected_body_type = user_input_body_type(image_dir)
    gender, age, height, weight, goal_weight, activity_scale = (
        input_current_user_stats()
    )
    daily_calorie_change = determine_daily_calorie_change(weight, goal_weight)

    st.write(
        f"To achieve your desired weight within the timeframe you will need to change your current caloric intake by: {daily_calorie_change:.0f} kcal."
    )

    display_calorie_change_studies()

    rdi_dict = calculate_nutrient_goals(
        weight=weight,
        height=height,
        age=age,
        calorie_adjustment=daily_calorie_change,
        activity_scale=activity_scale,
        gender=gender,
    )

    initialize_macro_rdi_session_state(rdi_dict)

st.markdown("### 2. Energy & Macros")
with st.expander("Energy Intake"):
    st.write(
        "You will receive a mealplan with a total energy intake within the following range:"
    )
    st.write(
        "(The default range is what is optimal based on the data you put in previously, but you can adjust it as needed)"
    )
    energy_intake, constant_kcal = user_input_energy(rdi_dict)

with st.expander("Macronutrients Ratio"):
    st.write(
        "You will receive a mealplan with macronutrients within the following range:"
    )
    st.write(
        "(The default range is optimal based on the data you put in previously, but you can adjust it as needed)"
    )
    col1, col2 = st.columns([1, 1])

    with col1:
        NUTRIENTS = ["Total Fat [G]", "Carbohydrate [G]", "Protein [G]"]
        macro_ranges = {}
        macro_ranges = user_input_macronutrients(
            macro_ranges, NUTRIENTS, slider_range=(0, 600), constant_kcal=constant_kcal
        )

with st.expander("Macronutrients Health Threats"):
    st.write(
        "You will receive a mealplan that caps the following unhealthy macronutrients within the following range:"
    )
    st.write(
        "(The default range is optimal based on the data you put in previously, but you can adjust it as needed)"
    )
    col1, col2 = st.columns([1, 1])

    with col1:
        NUTRIENTS = ["Sugars, added [G]", "Saturated Fat [G]"]
        macro_ranges = user_input_macronutrients(
            macro_ranges, NUTRIENTS, slider_range=(0, 100), constant_kcal=constant_kcal
        )


st.markdown("### 3. Fiber Intake")
with st.expander("Fiber Intake"):
    st.write(
        "You will receive a mealplan that contains fiber within the following range:"
    )
    st.write(
        "(The default range is optimal based on the data you put in previously, but you can adjust it as needed)"
    )
    col1, col2 = st.columns([1, 1])

    with col1:
        NUTRIENTS = ["Fiber [G]"]
        macro_ranges = user_input_macronutrients(
            macro_ranges, NUTRIENTS, slider_range=(0, 100), constant_kcal=constant_kcal
        )


st.markdown("### 4. Micronutrients")
with st.expander("Micronutrients"):

    micro_ranges = {}
    st.write(
        "You will receive a mealplan that micronutrients within the following range:"
    )
    st.write(
        "(The default range is optimal based on the data you put in previously, but you can adjust it as needed)"
    )
    col1, col2 = st.columns([1, 1])

    with col1:
        micro_ranges = user_input_micronutrients(rdi_dict, micro_ranges)

    if show_micronutrient_health_outcomes_bool:
        with col2:
            show_micronutrient_health_outcomes(
                rdi_dict, path="data/processed/nutrient_health_outcomes.csv"
            )


st.markdown("### 5. Optimization Settings")
with st.expander("Optimization Settings"):
    col_1, col_2 = st.columns([1, 1])
    with col_1:
        (
            cost_factor,
            time_factor,
            insulin_factor,
            fullness_factor,
            daily_food_budget,
            optimization_unit_size,
            micro_tolerance,
        ) = user_input_optimization_settings()

st.markdown("### 6. Food Preferences")
with st.expander("Food Preferences"):
    manage_constraints()

if st.button("Optimize Diet"):
    relative_df, food_vars = optimize_diet(
        daily_food_budget=daily_food_budget,
        cost_factor=cost_factor,
        time_factor=time_factor,
        insulin_factor=insulin_factor,
        fullness_factor=fullness_factor,
        df=df,
        rdi_dict=rdi_dict,
        food_constraints=st.session_state.food_constraints,
        optimization_unit_size=optimization_unit_size,
        macro_tolerance=0,
        micro_tolerance=micro_tolerance,
    )

    relative_df.to_csv("output/raw/relative_df.csv")

    # THESE RESULTS ARE RELATIVE TO THE RDI BOUNDS AND DEPEND ON optimization_unit_size!!!
    normalized_results_df, summary_df, total_df = (
        create_normalized_optimization_results_summary(relative_df, rdi_dict, food_vars)
    )

    absolute_results_df = create_absolute_optimization_results_summary(
        df, rdi_dict, food_vars, optimization_unit_size
    )
    # THESE RESULTS ARE RELATIVE TO THE RDI BOUNDS AND DEPEND ON optimization_unit_size!!!
    flat_column_normalized_result_df = save_optimization_results(
        normalized_raw_output_path, normalized_results_df
    )

    flat_column_absolute_result_df = save_optimization_results(
        absolute_raw_output_path, absolute_results_df
    )

    st.markdown("### Optimization Results")

    if show_mealplan:
        with st.expander("Your Optimized Daily Food Plan"):
            merged_df = create_meaplan_from_optimizer_results(
                df,
                flat_column_normalized_result_df,
                optimization_unit_size,
                directory=mealplan_path,
                streamlit_mealplan_columns=config["streamlit_mealplan_columns"],
            )
            display_mealplan_in_streamlit(merged_df)

    with st.expander("Nutritional Breakdown"):
        abs_sum_fig = create_absolute_summed_macronutrient_figure(
            absolute_raw_output_path
        )

        norm_sum_fig = create_normalized_summed_micronutrient_figure(
            absolute_raw_output_path, normalized_raw_output_path
        )
        st.plotly_chart(abs_sum_fig)
        st.plotly_chart(norm_sum_fig)

    with st.expander("Fully Detailed Nutritional Breakdown"):
        abs_stacked_fig = create_absolute_stacked_macronutrient_figure(
            absolute_raw_output_path
        )
        norm_stacked_fig = create_normalized_stacked_micronutrient_figure(
            absolute_raw_output_path, normalized_raw_output_path
        )
        st.plotly_chart(abs_stacked_fig)
        st.plotly_chart(norm_stacked_fig)

    if upload_spreadsheet:
        with open(args.spreadsheet_config, "r") as f:
            spreadsheet_config = yaml.safe_load(f)
            output_path = config["output_path"]

            wb = create_mealplan_spreadsheet(
                optimization_path,
                spreadsheet_columns=spreadsheet_config["columns"],
                output_path=config["output_path"],
            )

            output = io.BytesIO()
            wb.save(output)
            output.seek(0)  # Move the cursor to the beginning of the BytesIO object

            # Add a download button
            st.download_button(
                label="CLICK HERE TO DOWNLOAD: mealplan.xlsx",
                data=output,
                file_name="mealplan.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    if upload_shopping_list:
        with open(args.shopping_config, "r") as f:
            shopping_config = yaml.safe_load(f)

        df = pd.read_csv(shopping_config["paths"]["data"])

        wb_io = create_shopping_list_sheet(
            df,
            shopping_list_columns=shopping_config["columns"],
            output_path=shopping_config["paths"]["output"],
        )

        # Add a download button
        st.download_button(
            label="CLICK HERE TO DOWNLOAD: shopping_list.xlsx",
            data=wb_io,
            file_name="shopping_list.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
