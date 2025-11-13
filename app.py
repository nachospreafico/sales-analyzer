import streamlit as st
import pandas as pd

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

    st.dataframe(filtered_df)

    grouped_by_date = pd.DataFrame(filtered_df.groupby("Date", as_index=False)["Sales"].sum().sort_values("Date"))

    if filtered_df.empty:
        st.warning("No data for selected filters")
    else:
        st.line_chart(data=grouped_by_date, x="Date", y="Sales")
        sales_total_col, daily_sales_avg_col, max_sale_col = st.columns(3, border=True)
        with sales_total_col:
            sales_total = filtered_df["Sales"].sum()
            st.metric("Total Sales", f"${sales_total:,.2f}")
        with daily_sales_avg_col:
            daily_sales_avg = grouped_by_date["Sales"].mean()
            st.metric("Avg. Daily Sales", f"${daily_sales_avg:,.2f}")
        with max_sale_col:
            max_sale = grouped_by_date["Sales"].max()
            peak_day = grouped_by_date[grouped_by_date["Sales"] == max_sale]["Date"].tolist().dt.strftime("%Y-%m-%d")
            st.metric("Highest Sale", f"Peak Day: {peak_day} / Value: ${max_sale:,.2f}")
    

    
