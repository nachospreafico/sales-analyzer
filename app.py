import streamlit as st
import pandas as pd
from datetime import timedelta

st.set_page_config(
    page_title="Sales Forecast Visualizer",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Sales Forecast Visualizer")
st.subheader("Upload your sales data and visualize past trends with simple forecasts.")

uploaded_file = st.file_uploader("Upload a CSV file with columns: Date, Region, Product, Sales", type=["csv"])

needed_cols = ["Date", "Region", "Product", "Sales"]

if uploaded_file is None:
    st.info("Please upload a CSV to continue.")
    st.stop()

else:
    df = pd.read_csv(uploaded_file)
    df.columns = [col.strip() for col in df.columns.tolist()]
    df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
    for col in needed_cols:
        if col not in df.columns.tolist():
            st.error("Missing necessary column.")
            st.stop()
    st.success("CSV loaded successfully!")
    st.write(f"##### Rows: {df.shape[0]} x Columns: {df.shape[1]}")

    with st.sidebar:
        st.subheader("Filters")
        regions = sorted(df["Region"].unique().tolist())
        region_filter = st.multiselect("Region", options=regions)

        products = sorted(df["Product"].unique().tolist())
        product_filter = st.multiselect("Product", options=products)

        min_date, max_date = df["Date"].min().to_pydatetime(), df["Date"].max().to_pydatetime()
        date_filter = st.slider("Date", value=(min_date, max_date))
        start_date, end_date = date_filter[0], date_filter[1]

    filtered_df = df.copy()

    if region_filter:
        filtered_df = filtered_df[filtered_df["Region"].isin(region_filter)]
    
    if product_filter:
        filtered_df = filtered_df[filtered_df["Product"].isin(product_filter)]

    filtered_df = filtered_df[(filtered_df["Date"] >= start_date) & (filtered_df["Date"] <= end_date)]

    with st.expander("Show filtered raw data"):
        st.dataframe(filtered_df)

    st.divider()

    grouped_by_date = pd.DataFrame(filtered_df.groupby("Date", as_index=False)["Sales"].sum().sort_values("Date"))

    if filtered_df.empty:
        st.warning("No data for selected filters")
    else:
        st.subheader("Sales Over Time")
        st.line_chart(data=grouped_by_date, x="Date", y="Sales")

        st.divider()

        st.subheader("Key Metrics")
        sales_total_col, daily_sales_avg_col, max_sale_col = st.columns(3, border=True)
        with sales_total_col:
            sales_total = filtered_df["Sales"].sum()
            st.metric("Total Sales", f"${sales_total:,.2f}")
        with daily_sales_avg_col:
            daily_sales_avg = grouped_by_date["Sales"].mean()
            st.metric("Avg. Daily Sales", f"${daily_sales_avg:,.2f}")
        with max_sale_col:
            max_sale = grouped_by_date["Sales"].max()
            peak_day = grouped_by_date[grouped_by_date["Sales"] == max_sale]["Date"].tolist()[-1].strftime("%Y-%m-%d")
            st.metric(f"Peak Day: {peak_day}", value=f"${max_sale:,.2f}")

        st.divider()

        st.subheader("Breakdown by Product")
        grouped_by_product = filtered_df.groupby("Product", as_index=False)["Sales"].sum()

        st.bar_chart(data=grouped_by_product, x="Product", y="Sales", color="Product")

        st.divider()

        st.subheader("Breakdown by Region")
        grouped_by_region = filtered_df.groupby("Region", as_index=False)["Sales"].sum()

        st.bar_chart(data=grouped_by_region, x="Region", y="Sales", color="Region")

        st.divider()

        st.subheader("Simple Forecast (Experimental)")
        st.write("This section provides a simple baseline forecast using recent sales trends. It is not a production model, but it helps visualize how sales might evolve in the near future based on past patterns.")

        forecast_horizon = st.slider("Forecast Horizon (days)", min_value=7, max_value=60, value=14)

        last_day = grouped_by_date["Date"].max()
        first_day_of_fcst_horizon = last_day + timedelta(days=1)

        forecast_range = pd.date_range(start=first_day_of_fcst_horizon, periods=forecast_horizon)
        
        forecast_df = pd.DataFrame({
            "Date": forecast_range,
        })

        forecast_df["Naive Forecast"] = grouped_by_date['Sales'].iloc[-1]

        last_7_days = grouped_by_date['Sales'].iloc[-7:].mean()

        forecast_df["Moving Average"] = last_7_days

        hist_and_fcst_df = pd.concat([grouped_by_date, forecast_df])

        hist_and_fcst_df = hist_and_fcst_df.rename(columns={"Sales": "Actuals"})

        forecast_options = [col for col in hist_and_fcst_df.columns.tolist() if col != "Date"]
        
        selected_forecast = st.multiselect("Select series to display on the line chart", options=forecast_options, default=forecast_options)

        st.line_chart(data=hist_and_fcst_df, x="Date", y=selected_forecast)

        st.divider()

        st.subheader("Model Performance")

        grouped_by_date = grouped_by_date.rename(columns={"Sales": "Actuals"})

        grouped_by_date["Naive Prediction"] = grouped_by_date["Actuals"].shift(1)

        grouped_by_date["Absolute Error"] = abs(grouped_by_date["Actuals"] - grouped_by_date["Naive Prediction"])

        grouped_by_date["Squared Error"] = (grouped_by_date["Actuals"] - grouped_by_date["Naive Prediction"]) ** 2

        filtered_grouped_by_date = grouped_by_date.iloc[1:]

        st.dataframe(filtered_grouped_by_date)

        st.write("##### Naive Model")

        mae_col, rmse_col, mape_col = st.columns(3, border=True)

        mae = filtered_grouped_by_date["Absolute Error"].mean()

        mse = filtered_grouped_by_date["Squared Error"].mean()

        rmse = mse**0.5

        filtered_grouped_by_date_for_mape = filtered_grouped_by_date[filtered_grouped_by_date["Actuals"] != 0]

        ape = filtered_grouped_by_date_for_mape["Absolute Error"] / filtered_grouped_by_date_for_mape["Actuals"]

        mape = (ape * 100).mean()

        with mae_col:
            st.metric("MAE", f"{mae:,.2f}", help="Mean Absolute Error: average size of the errors, in the same units as the target. Lower is better.")
        
        with rmse_col:
            st.metric("RMSE", f"{rmse:,.2f}", help="Root Mean Squared Error: penalizes large errors more strongly. Useful when big misses matter. Lower is better.")
        
        with mape_col:
            st.metric("MAPE", f"{mape:,.2f}%", help="Mean Absolute Percentage Error: shows the average error as a percentage of actuals. Interpretable but unstable when actuals are near zero.")