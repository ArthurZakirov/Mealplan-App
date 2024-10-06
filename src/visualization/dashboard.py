import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


def visualize_optimization_result_nutrient_breakdown(results_df):
    macro_df = pd.concat(
        [
            results_df[["Macronutrient"]],
            results_df[[("Non Nutrient Data", "Optimal Quantity")]],
        ],
        axis=1,
    )
    macro_df = macro_df.set_index(results_df[("Non Nutrient Data", "FDC Name")].values)
    macro_df = macro_df[~macro_df.index.isin(["Total", "Lower Bound", "Upper Bound"])]
    macro_df.columns = macro_df.columns.get_level_values(1)
    macro_df = macro_df.drop(columns=["Optimal Quantity"])
    df_t = macro_df.transpose()

    macro_fig = px.bar(
        df_t,
        x=df_t.index,
        y=df_t.columns,
        title="Nutrient Contributions by Food",
        labels={"index": "Nutrients", "value": "Total Amount", "variable": "Food"},
        orientation="v",
    )

    # Customize the layout
    macro_fig.update_layout(
        barmode="stack",
        xaxis_title="Nutrients",
        yaxis_title="Total Macronutrient Amount (% of RDI)",
        legend_title="Foods",
    )

    micro_df = pd.concat(
        [
            results_df[["Micronutrient"]],
            results_df[[("Non Nutrient Data", "Optimal Quantity")]],
        ],
        axis=1,
    )
    micro_df = micro_df.set_index(results_df[("Non Nutrient Data", "FDC Name")].values)
    micro_df = micro_df[~micro_df.index.isin(["Total", "Lower Bound", "Upper Bound"])]
    micro_df.columns = micro_df.columns.get_level_values(1)
    micro_df = micro_df.drop(columns=["Optimal Quantity"])
    df_t = micro_df.transpose()

    micro_fig = px.bar(
        df_t,
        x=df_t.index,
        y=df_t.columns,
        title="Nutrient Contributions by Food",
        labels={"index": "Nutrients", "value": "Total Amount", "variable": "Food"},
        orientation="v",
    )

    # Customize the layout
    micro_fig.update_layout(
        barmode="stack",
        xaxis_title="Nutrients",
        yaxis_title="Total Micronutrient Amount (% of RDI)",
        legend_title="Foods",
    )

    return macro_fig, micro_fig


def visualize_polar_chart(df, names):
    macro_df = df.copy()
    macro_df.columns = macro_df.columns.get_level_values(1)
    macro_df = macro_df[
        [
            "FDC Name",
            "Energy [KCAL]",
            "Carbohydrate [G]",
            "Fiber [G]",
            "Protein [G]",
            "Total Fat [G]",
        ]
    ]

    max_values = df.loc[:, df.columns.get_level_values(1) != "FDC Name"].max()

    scaler = MinMaxScaler()
    polar_df = macro_df.copy()
    polar_df.loc[:, polar_df.columns != "FDC Name"] = scaler.fit_transform(
        macro_df.loc[:, macro_df.columns != "FDC Name"]
    )

    fig = go.Figure()

    for name in names:
        index = macro_df[macro_df["FDC Name"] == name].index.values[0]

        fig.add_trace(
            go.Scatterpolar(
                r=polar_df.drop(columns="FDC Name").loc[index],
                theta=polar_df.columns.difference(["FDC Name"]),
                fill="toself",
                name=polar_df.loc[index, "FDC Name"],
            )
        )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                # Set ticktext to empty to hide labels
                tickvals=np.linspace(0, 1.2, num=5),
                ticktext=[
                    "" for _ in np.linspace(0, 1, num=5)
                ],  # Empty strings for each tick
            ),
            angularaxis=dict(
                tickvals=np.arange(len(polar_df.columns.difference(["FDC Name"]))),
                ticktext=[
                    f"{category} (max: {int(macro_df.max(axis=0)[category])})"
                    for category in polar_df.columns.difference(["FDC Name"])
                ],
            ),
        ),
        title=f"Nutritional values per 100g",
    )
    fig.update_layout(
        autosize=False,
        width=800,
        height=800,
    )
    return fig


def visualize_micronutrient_polar_chart(relative_df, names):
    macro_df = relative_df.copy()
    macro_df.columns = macro_df.columns.get_level_values(1)
    macro_df = macro_df[["FDC Name"] + relative_df["Micronutrient"].columns.to_list()]

    polar_df = macro_df

    fig = go.Figure()

    for name in names:
        index = macro_df[macro_df["FDC Name"] == name].index.values[0]

        fig.add_trace(
            go.Scatterpolar(
                r=polar_df.drop(columns="FDC Name").loc[index],
                theta=polar_df.columns.difference(["FDC Name"]),
                fill="toself",
                name=polar_df.loc[index, "FDC Name"],
            )
        )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                # Set ticktext to empty to hide labels
                tickvals=np.linspace(0, 1.2, num=5),
                ticktext=[
                    "" for _ in np.linspace(0, 1, num=5)
                ],  # Empty strings for each tick
            ),
            angularaxis=dict(
                tickvals=np.arange(len(polar_df.columns.difference(["FDC Name"]))),
                ticktext=[
                    f"{category} (max: {int(macro_df.max(axis=0)[category])})"
                    for category in polar_df.columns.difference(["FDC Name"])
                ],
            ),
        ),
        title=f"Nutritional values per 100g",
    )
    fig.update_layout(
        autosize=False,
        width=800,
        height=800,
    )
    return fig


def nutrition_scatter_plot(df, x_col, y_col, z_col, title, delimiter=", "):
    x_col_str = delimiter.join(x_col).strip()
    y_col_str = delimiter.join(y_col).strip()
    z_col_str = delimiter.join(z_col).strip()

    plotly_df = df.copy()
    plotly_df.columns = [", ".join(col).strip() for col in df.columns.values]
    fig = px.scatter(
        plotly_df,
        x=x_col_str,
        y=y_col_str,
        color=z_col_str,
        color_continuous_scale=px.colors.sequential.Viridis,
        hover_name="Non Nutrient Data, FDC Name",
        hover_data={x_col_str: True, y_col_str: True},
        labels={x_col_str: x_col_str, y_col_str: y_col_str},
        title=title,
    )

    return fig


def create_normalized_summed_micronutrient_figure(
    absolute_raw_output_path, normalized_raw_output_path
):
    # Load your data
    df_abs = pd.read_csv(absolute_raw_output_path)
    df_abs.columns = pd.MultiIndex.from_tuples(
        [tuple(c.split(".")) for c in df_abs.columns]
    )
    df_abs_micro = df_abs["Micronutrient"].sum().to_frame().T

    df_norm = pd.read_csv(normalized_raw_output_path)
    df_norm.columns = pd.MultiIndex.from_tuples(
        [tuple(c.split(".")) for c in df_norm.columns]
    )
    df_norm_micro = df_norm["Micronutrient"].sum().to_frame().T

    # Define categories for micronutrients
    micronutrient_categories = {
        "Vitamins": [
            "Vitamin A [UG]",
            "Vitamin B-12 [UG]",
            "Vitamin B-6 [MG]",
            "Vitamin C [MG]",
            "Vitamin E [MG]",
            "Vitamin K [UG]",
        ],
        "Minerals": [
            "Calcium [MG]",
            "Copper [MG]",
            "Iron [MG]",
            "Magnesium [MG]",
            "Manganese [MG]",
            "Phosphorus [MG]",
            "Potassium [MG]",
            "Selenium [UG]",
            "Sodium [MG]",
            "Zinc [MG]",
        ],
        "Other Micronutrients": ["Choline [MG]", "Folate [UG]", "Niacin [MG]"],
    }

    BAR_HEIGHT = 40  # Bar height in pixels
    total_bars = sum(
        [len(nutrients) for nutrients in micronutrient_categories.values()]
    )
    total_plot_height = BAR_HEIGHT * total_bars

    # Create subplots for each category with dynamic row heights
    row_heights = [
        len(nutrients) / total_bars for nutrients in micronutrient_categories.values()
    ]
    fig = make_subplots(
        rows=len(micronutrient_categories),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=row_heights,
    )

    # Add a bar chart for each category
    for i, (category, nutrients) in enumerate(micronutrient_categories.items(), 1):
        percentages = df_norm_micro.loc[
            :, nutrients
        ].values.flatten()  # Get normalized values
        abs_values = df_abs_micro.loc[:, nutrients].values.flatten()

        # Convert to percentage and to int
        percentages_int = (percentages).astype(
            int
        )  # Convert to percentage and then to int

        fig.add_trace(
            go.Bar(
                x=percentages_int,  # Use integer percentages
                y=nutrients,
                orientation="h",
                text=[
                    f"{val}%" for val in percentages_int
                ],  # Display normalized values as integers with "%"
                textposition="inside",  # Position text inside the bars
                hoverinfo="text",  # Show hover information
                hovertext=[
                    f"{val:.2f} mg" for val in abs_values
                ],  # Absolute values in hover
                marker=dict(
                    color=["yellow" if x <= 100 else "green" for x in percentages]
                ),
                showlegend=False,  # Disable legend for this trace
            ),
            row=i,
            col=1,
        )

        # Add a 100% reference line
        fig.add_shape(
            type="line",
            x0=100,
            x1=100,
            y0=-0.5,
            y1=len(nutrients) - 0.5,
            line=dict(color="black", width=5, dash="dash"),
            row=i,
            col=1,
        )

        # Set y-axis title for the current subplot
        fig.update_yaxes(title_text=category, row=i, col=1)

    # Update layout for the entire figure
    fig.update_layout(
        title="Micronutrient % of RDI",
        height=total_plot_height,  # Total plot height is dynamically set based on number of bars
        width=800,
        bargap=0.1,  # Consistent gap between bars
    )

    return fig


def create_normalized_stacked_micronutrient_figure(
    absolute_raw_output_path, normalized_raw_output_path
):
    # Load your data
    df_abs = pd.read_csv(absolute_raw_output_path)
    df_abs.columns = pd.MultiIndex.from_tuples(
        [tuple(c.split(".")) for c in df_abs.columns]
    )
    df_abs_micro = df_abs["Micronutrient"]  # Keep individual food contributions

    df_norm = pd.read_csv(normalized_raw_output_path)
    df_norm.columns = pd.MultiIndex.from_tuples(
        [tuple(c.split(".")) for c in df_norm.columns]
    )
    df_norm_micro = df_norm["Micronutrient"]  # Keep individual food contributions

    # Extract food names for the legend and hovertext
    food_names = df_abs["Non Nutrient Data"]["FDC Name"]

    # Define categories for micronutrients
    micronutrient_categories = {
        "Vitamins": [
            "Vitamin A [UG]",
            "Vitamin B-12 [UG]",
            "Vitamin B-6 [MG]",
            "Vitamin C [MG]",
            "Vitamin E [MG]",
            "Vitamin K [UG]",
        ],
        "Minerals": [
            "Calcium [MG]",
            "Copper [MG]",
            "Iron [MG]",
            "Magnesium [MG]",
            "Manganese [MG]",
            "Phosphorus [MG]",
            "Potassium [MG]",
            "Selenium [UG]",
            "Sodium [MG]",
            "Zinc [MG]",
        ],
        "Other Micronutrients": ["Choline [MG]", "Folate [UG]", "Niacin [MG]"],
    }

    BAR_HEIGHT = 40  # Bar height in pixels
    total_bars = sum(
        [len(nutrients) for nutrients in micronutrient_categories.values()]
    )
    total_plot_height = BAR_HEIGHT * total_bars

    # Create subplots for each category with dynamic row heights
    row_heights = [
        len(nutrients) / total_bars for nutrients in micronutrient_categories.values()
    ]
    fig = make_subplots(
        rows=len(micronutrient_categories),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=row_heights,
    )

    # Add a stacked bar chart for each category
    for i, (category, nutrients) in enumerate(micronutrient_categories.items(), 1):
        for food_idx, food in enumerate(
            df_abs_micro.index
        ):  # Iterate over foods to stack the bars
            percentages = df_norm_micro.loc[
                food, nutrients
            ].values.flatten()  # Get normalized values for each food
            abs_values = df_abs_micro.loc[
                food, nutrients
            ].values.flatten()  # Get absolute values for each food

            # Use food name for the legend and hovertext
            food_name = food_names[food_idx]

            fig.add_trace(
                go.Bar(
                    x=percentages,  # Use normalized percentages for stacking
                    y=nutrients,
                    orientation="h",
                    hoverinfo="text",  # Show hover information
                    hovertext=[
                        f"{food_name}: {val:.2f} mg / µg" for val in abs_values
                    ],  # Absolute values with food names in hover
                    name=food_name,  # Use food name from the "Non Nutrient Data.FDC Name" column
                    showlegend=True,  # Enable legend to show food contributions
                ),
                row=i,
                col=1,
            )

        # Add a 100% reference line
        fig.add_shape(
            type="line",
            x0=100,
            x1=100,
            y0=-0.5,
            y1=len(nutrients) - 0.5,
            line=dict(color="black", width=5, dash="dash"),
            row=i,
            col=1,
        )

        # Set y-axis title for the current subplot
        fig.update_yaxes(title_text=category, row=i, col=1)

    # Update layout for the entire figure
    fig.update_layout(
        title="Micronutrient % of RDI by Food",
        height=total_plot_height,  # Total plot height is dynamically set based on number of bars
        width=800,
        bargap=0.1,  # Consistent gap between bars
        barmode="stack",  # Enable stacking of bars
    )

    return fig


def create_absolute_summed_macronutrient_figure(absolute_raw_output_path):
    # Read and structure absolute data
    df_abs = pd.read_csv(absolute_raw_output_path)
    df_abs = df_abs.apply(
        lambda col: col.astype("int") if pd.api.types.is_numeric_dtype(col) else col
    )
    df_abs.columns = pd.MultiIndex.from_tuples(
        [tuple(c.split(".")) for c in df_abs.columns]
    )

    df_abs_micro = df_abs["Micronutrient"].sum().to_frame().T
    df_abs_macro = df_abs["Macronutrient"].sum().to_frame().T

    # Get absolute values for Protein, Total Fat, and Carbohydrate
    protein_g = df_abs_macro["Protein [G]"].values[0]
    total_fat_g = df_abs_macro["Total Fat [G]"].values[0]
    carbohydrate_g = df_abs_macro["Carbohydrate [G]"].values[0]

    # Calculate kcalories
    protein_kcal = protein_g * 4
    total_fat_kcal = total_fat_g * 9
    carbohydrate_kcal = carbohydrate_g * 4
    total_kcal = protein_kcal + total_fat_kcal + carbohydrate_kcal

    # Prepare data for the stacked bar chart
    labels = ["Protein", "Total Fat", "Carbohydrate"]
    values_g = [protein_g, total_fat_g, carbohydrate_g]
    values_kcal = [protein_kcal, total_fat_kcal, carbohydrate_kcal]

    # Create the stacked bar chart for macronutrients
    fig_macro = go.Figure()

    # Add bars for each macronutrient
    fig_macro.add_trace(
        go.Bar(
            x=labels,
            y=[protein_kcal],
            name="Protein",
            text=[f"{protein_g} g"],
            textposition="auto",
        )
    )

    fig_macro.add_trace(
        go.Bar(
            x=labels,
            y=[total_fat_kcal],
            name="Total Fat",
            text=[f"{total_fat_g} g"],
            textposition="auto",
        )
    )

    fig_macro.add_trace(
        go.Bar(
            x=labels,
            y=[carbohydrate_kcal],
            name="Carbohydrate",
            text=[f"{carbohydrate_g} g"],
            textposition="auto",
        )
    )

    # Update layout for macronutrients
    fig_macro.update_layout(
        title="Macronutrient Distribution by kcal",
        xaxis_title="Macronutrient",
        yaxis_title="Total kcal",
        barmode="stack",
        height=400,
        width=400,
        font=dict(color="black"),
    )

    # Add total kcal annotation
    fig_macro.add_annotation(
        x=0.5,
        y=total_kcal + 300,
        text=f"Total kcal: {total_kcal}",
        showarrow=False,
        font=dict(size=14, color="black"),
        xref="paper",
        yref="y",
    )

    return fig_macro


def create_absolute_stacked_macronutrient_figure(absolute_raw_output_path):
    # Load your data
    df_abs = pd.read_csv(absolute_raw_output_path)
    df_abs.columns = pd.MultiIndex.from_tuples(
        [tuple(c.split(".")) for c in df_abs.columns]
    )
    df_abs_macro = df_abs[
        "Macronutrient"
    ]  # Keep individual food contributions for macronutrients

    # Extract food names for the legend and hovertext
    food_names = df_abs["Non Nutrient Data"]["FDC Name"]

    # Define macronutrients and fiber
    macronutrient_categories = {
        "Macronutrients": ["Carbohydrate [G]", "Total Fat [G]", "Protein [G]"],
        "Fiber": ["Fiber [G]"],
    }

    BAR_HEIGHT = 100  # Bar height in pixels
    total_bars = sum(
        [len(nutrients) for nutrients in macronutrient_categories.values()]
    )
    total_plot_height = BAR_HEIGHT * total_bars

    # Create subplots: one for Macronutrients and one for Fiber
    row_heights = [
        len(nutrients) / total_bars for nutrients in macronutrient_categories.values()
    ]
    fig = make_subplots(
        rows=len(macronutrient_categories),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=row_heights,
    )

    # Add a stacked bar chart for Macronutrients and Fiber
    for i, (category, nutrients) in enumerate(macronutrient_categories.items(), 1):
        for food_idx, food in enumerate(
            df_abs_macro.index
        ):  # Iterate over foods to stack the bars
            abs_values = df_abs_macro.loc[
                food, nutrients
            ].values.flatten()  # Get absolute values for each food

            # Use food name for the legend and hovertext
            food_name = food_names[food_idx]

            fig.add_trace(
                go.Bar(
                    x=abs_values,  # Use absolute values for stacking
                    y=nutrients,
                    orientation="h",
                    hoverinfo="text",  # Show hover information
                    hovertext=[
                        f"{food_name}: {val:.2f} g" for val in abs_values
                    ],  # Absolute values with food names in hover
                    name=food_name,  # Use food name from the "Non Nutrient Data.FDC Name" column
                    showlegend=True,  # Enable legend to show food contributions
                ),
                row=i,
                col=1,
            )

        # Set y-axis title for the current subplot
        fig.update_yaxes(title_text=category, row=i, col=1)

    # Update layout for the entire figure
    fig.update_layout(
        title="Macronutrient and Fiber Content by Food",
        height=total_plot_height,  # Total plot height is dynamically set based on number of bars
        width=800,
        bargap=0.1,  # Consistent gap between bars
        barmode="stack",  # Enable stacking of bars
    )

    return fig
