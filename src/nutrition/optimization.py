import pulp as pl
import pandas as pd


def calculate_relative_nutrient_df(df, rdi_dict, optimization_unit_size=100, goal=100):

    ################
    # Flatten the RDI bounds
    flat_rdi_lower_bound = {}
    flat_rdi_upper_bound = {}

    for category, nutrients in rdi_dict.items():
        for nutrient, bounds in nutrients.items():
            if bounds["lower_bound"] is not None and bounds["lower_bound"] > 0:
                flat_rdi_lower_bound[(category, nutrient)] = bounds["lower_bound"]
            if "upper_bound" in bounds and bounds["upper_bound"] is not None:
                flat_rdi_upper_bound[(category, nutrient)] = bounds["upper_bound"]

    # Calculate percentages relative to the bounds
    percentage_df = pd.DataFrame(index=df.index)
    for col in df.columns:
        if col in flat_rdi_lower_bound:
            # Calculate percentage relative to the lower bound
            percentage_df[col] = (df[col] / flat_rdi_lower_bound[col]) * goal
        elif col in flat_rdi_upper_bound:
            # Calculate percentage relative to the upper bound if the lower bound is None
            percentage_df[col] = (df[col] / flat_rdi_upper_bound[col]) * goal
        else:
            # Copy non-nutrient data as is
            percentage_df[col] = df[col]

        if col[0] != "Non Nutrient Data":
            # Multiply by the amount unit to get the actual amount
            percentage_df[col] = percentage_df[col] * optimization_unit_size / 100

    percentage_df.columns = pd.MultiIndex.from_tuples(
        [x for x in percentage_df.columns]
    )
    percentage_df
    return percentage_df, flat_rdi_lower_bound, flat_rdi_upper_bound


import pulp as pl
import streamlit as st


def optimize_diet(
    daily_food_budget,
    cost_factor,
    time_factor,
    insulin_factor,
    fullness_factor,
    df,
    rdi_dict,
    food_constraints,
    optimization_unit_size,
    macro_tolerance=0,
    micro_tolerance=10,
):
    goal = 100
    normalized_df, flat_rdi_lower_bound, flat_rdi_upper_bound = (
        calculate_relative_nutrient_df(df, rdi_dict, optimization_unit_size, goal)
    )

    # Create the optimization model
    model = pl.LpProblem("Diet_Optimization", pl.LpMinimize)

    # Decision variables: Amounts of each food item to consume
    food_vars = pl.LpVariable.dicts(
        "Food", normalized_df.index, lowBound=0, cat=pl.LpInteger
    )

    ###########################################
    # UTILITY FUNCTION
    ###########################################

    total_cost = pl.lpSum(
        [
            optimization_unit_size
            / 100
            * normalized_df.loc[i, ("Non Nutrient Data", "Price per 100g")]
            * food_vars[i]
            for i in normalized_df.index
        ]
    )

    total_time = pl.lpSum(
        [
            normalized_df.loc[i, ("Non Nutrient Data", "Preparation Time")]
            * food_vars[i]
            for i in normalized_df.index
        ]
    )

    total_insulin = pl.lpSum(
        [
            normalized_df.loc[i, ("Non Nutrient Data", "Insulin Index")]
            * food_vars[i]
            * (
                (optimization_unit_size / 100)
                * normalized_df.loc[i, ("Energy", "Energy [KCAL]")]
                * 4.184
                / 1000
            )
            for i in normalized_df.index
        ]
    )

    total_fullness = pl.lpSum(
        [
            normalized_df.loc[i, ("Non Nutrient Data", "Fullness Factor")]
            * (
                (optimization_unit_size / 100)
                * normalized_df.loc[i, ("Energy", "Energy [KCAL]")]
            )
            * food_vars[i]
            for i in normalized_df.index
        ]
    )

    # Add the budget constraint
    model += (total_cost <= daily_food_budget, "Budget_Constraint")

    # Add the utility function to the objective
    utility_function = (
        cost_factor * total_cost
        + time_factor * total_time
        + insulin_factor * total_insulin
        + fullness_factor * total_fullness
    )
    model += utility_function

    ###########################################
    # CONSTRAINTS
    ###########################################
    # Apply food constraints (min and max amounts)
    for food_name, limits in food_constraints.items():
        min_amt, max_amt = limits
        for i in normalized_df.index[
            normalized_df[("Non Nutrient Data", "FDC Name")] == food_name
        ]:
            if min_amt is not None:
                model += (food_vars[i] >= min_amt, f"{food_name}_min")
            if max_amt is not None:
                model += (food_vars[i] <= max_amt, f"{food_name}_max")

    # Extract macronutrient and micronutrient columns
    macronutrients = [
        col
        for col in normalized_df.columns
        if (col[0] == "Macronutrient" or col[0] == "Energy")
    ]
    micronutrients = [col for col in normalized_df.columns if col[0] == "Micronutrient"]

    # Apply macronutrient constraints
    for nutrient in macronutrients:
        if nutrient in flat_rdi_lower_bound:
            model += (
                pl.lpSum(
                    [
                        normalized_df.loc[i, nutrient] * food_vars[i]
                        for i in normalized_df.index
                    ]
                )
                >= 100 - macro_tolerance,
                f"{nutrient}_min",
            )
            if nutrient in flat_rdi_upper_bound:
                upper_bound_goal = (
                    flat_rdi_upper_bound[nutrient] / flat_rdi_lower_bound[nutrient]
                ) * 100
                model += (
                    pl.lpSum(
                        [
                            normalized_df.loc[i, nutrient] * food_vars[i]
                            for i in normalized_df.index
                        ]
                    )
                    <= upper_bound_goal + macro_tolerance,
                    f"{nutrient}_max",
                )

    # Apply micronutrient constraints
    for nutrient in micronutrients:
        model += (
            pl.lpSum(
                [
                    normalized_df.loc[i, nutrient] * food_vars[i]
                    for i in normalized_df.index
                ]
            )
            >= 100 - micro_tolerance,
            f"{nutrient}_min",
        )
        if nutrient in flat_rdi_upper_bound:
            upper_bound_goal = (
                flat_rdi_upper_bound[nutrient] / flat_rdi_lower_bound[nutrient]
            ) * 100
            model += (
                pl.lpSum(
                    [
                        normalized_df.loc[i, nutrient] * food_vars[i]
                        for i in normalized_df.index
                    ]
                )
                <= upper_bound_goal + micro_tolerance,
                f"{nutrient}_max",
            )

    # Solve the model
    model.solve()

    # Display the result
    if pl.LpStatus[model.status] == "Optimal":
        st.write("Optimization completed successfully!")
    else:
        st.error(
            "Your desired constraints are impossible to satisfy. "
            "Please relax the constraints and try again."
        )

    return normalized_df, food_vars


def create_absolute_optimization_results_summary(
    df, rdi_dict, food_vars=None, optimization_unit_size=1
):
    if not (food_vars is None):
        results = []
        for i in df.index:
            quantity = pl.value(food_vars[i])
            if (
                quantity is not None and quantity > 0
            ):  # Only consider food items with a non-zero quantity
                result_entry = {
                    ("Non Nutrient Data", "FDC Name"): df.loc[
                        i, ("Non Nutrient Data", "FDC Name")
                    ],
                    ("Non Nutrient Data", "Optimal Quantity"): quantity,
                }
                # Add nutrient data dynamically handling MultiIndex
                for nutrient in df.columns:
                    if nutrient[0] != "Non Nutrient Data":  # Exclude non-nutrient data
                        result_entry[nutrient] = (
                            df.loc[i, nutrient]
                            * quantity
                            * optimization_unit_size
                            / 100
                        )
                    else:
                        result_entry[nutrient] = df.loc[i, nutrient]

                results.append(result_entry)

        # Create DataFrame from results
        result_df = pd.DataFrame(results)
        return result_df


def create_normalized_optimization_results_summary(df, rdi_dict, food_vars=None):
    """
    THESE RESULTS ARE RELATIVE TO THE RDI BOUNDS and depend on optimization unit size!!!
    """
    # Extract the solution into a DataFrame

    if not (food_vars is None):
        results = []
        for i in df.index:
            quantity = pl.value(food_vars[i])
            if (
                quantity is not None and quantity > 0
            ):  # Only consider food items with a non-zero quantity
                result_entry = {
                    ("Non Nutrient Data", "FDC Name"): df.loc[
                        i, ("Non Nutrient Data", "FDC Name")
                    ],
                    ("Non Nutrient Data", "Optimal Quantity"): quantity,
                }
                # Add nutrient data dynamically handling MultiIndex
                for nutrient in df.columns:
                    if nutrient[0] != "Non Nutrient Data":  # Exclude non-nutrient data
                        result_entry[nutrient] = df.loc[i, nutrient] * quantity

                results.append(result_entry)

        # Create DataFrame from results
        result_df = pd.DataFrame(results)

        # Calculate total nutritional intake from selected items
        totals = {
            ("Non Nutrient Data", "FDC Name"): "Total",
            **{
                nutrient: sum(result_df[nutrient])
                for nutrient in df.columns
                if nutrient[0] != "Non Nutrient Data"
            },
        }

        # Create DataFrame for the total and goal rows
        totals_df = pd.DataFrame([totals])

    else:
        totals_df = pd.DataFrame()

    goal = 100

    flat_rdi_lower_bound = {}
    flat_rdi_upper_bound = {}

    for category, nutrients in rdi_dict.items():
        for nutrient, bounds in nutrients.items():
            if bounds["lower_bound"] is not None:
                flat_rdi_lower_bound[(category, nutrient)] = bounds["lower_bound"]
            if "upper_bound" in bounds and bounds["upper_bound"] is not None:
                flat_rdi_upper_bound[(category, nutrient)] = bounds["upper_bound"]

    flat_rdi_upper_bound_rel = {}
    flat_rdi_lower_bound_rel = {}

    for category, nutrients in rdi_dict.items():
        for nutrient, bounds in nutrients.items():
            if (bounds["lower_bound"] is None) and (bounds["upper_bound"] is not None):
                flat_rdi_upper_bound_rel[(category, nutrient)] = 100
                flat_rdi_lower_bound_rel[(category, nutrient)] = 0

            if (bounds["lower_bound"] is not None) and (bounds["upper_bound"] is None):
                flat_rdi_upper_bound_rel[(category, nutrient)] = float("inf")
                flat_rdi_lower_bound_rel[(category, nutrient)] = 100

            if (bounds["lower_bound"] is not None) and (
                bounds["upper_bound"] is not None
            ):
                flat_rdi_upper_bound_rel[(category, nutrient)] = (
                    flat_rdi_upper_bound[(category, nutrient)]
                    / flat_rdi_lower_bound[(category, nutrient)]
                ) * 100
                flat_rdi_lower_bound_rel[(category, nutrient)] = 100

    lower_bound = {
        nutrient: flat_rdi_lower_bound_rel[nutrient]
        for nutrient in df.columns
        if nutrient[0] != "Non Nutrient Data"
    }
    lower_bound[("Non Nutrient Data", "FDC Name")] = "Lower Bound"
    lower_bound[("Non Nutrient Data", "FDC Name")] = "Lower Bound"
    lower_bound_df = pd.DataFrame([lower_bound])

    upper_bound = {
        nutrient: flat_rdi_upper_bound_rel[nutrient]
        for nutrient in df.columns
        if nutrient[0] != "Non Nutrient Data"
    }
    upper_bound[("Non Nutrient Data", "FDC Name")] = "Upper Bound"
    upper_bound[("Non Nutrient Data", "FDC Name")] = "Upper Bound"
    upper_bound_df = pd.DataFrame([upper_bound])

    # Concatenate all together with 'Name' and 'Category' as a regular column
    summary_df = pd.concat(
        [totals_df, lower_bound_df, upper_bound_df], ignore_index=True
    )
    summary_df.columns = pd.MultiIndex.from_tuples(summary_df.columns)
    result_df.columns = pd.MultiIndex.from_tuples(result_df.columns)

    def convert_to_int(x):
        try:
            return int(x) if pd.notnull(x) else x
        except:
            return x

    # Apply the conversion across the DataFrame
    result_df = result_df.applymap(convert_to_int)
    total_df = pd.concat([summary_df, result_df], axis=0)
    return result_df, summary_df, total_df


def save_optimization_results(output_path, results_df):
    flat_column_normalized_result_df = results_df.copy()
    flat_column_normalized_result_df.columns = [
        f"{col[0]}.{col[1]}" for col in flat_column_normalized_result_df.columns
    ]
    flat_column_normalized_result_df.to_csv(output_path, index=False, encoding="utf-8")
    return flat_column_normalized_result_df
