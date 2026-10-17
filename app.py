
import streamlit as st
import pandas as pd
import plotly.express as px

# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================
st.set_page_config(
    page_title="RetailPulse Dashboard",
    page_icon="📊",
    layout="wide"
)

# =====================================================
# 2. DASHBOARD STYLE
# =====================================================
st.markdown("""
<style>
    .stApp {
        background-color: #F4F7FB;
    }
    [data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #DCE3EC;
        padding: 16px;
        border-radius: 12px;
    }
    [data-testid="stMetricLabel"] {
        color: #344054 !important;
    }
    [data-testid="stMetricValue"] {
        color: #17365D !important;
    }
    h1, h2, h3 {
        color: #17365D;
    }
</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. LOAD EXCEL DATA
# =====================================================
@st.cache_data
def load_data():
    file_name = "cleaned_online_retail.xlsx"

    sheet_1 = pd.read_excel(
        file_name,
        sheet_name="2009-10"
    )

    sheet_2 = pd.read_excel(
        file_name,
        sheet_name="2010-11"
    )

    # Combine both sheets
    data = pd.concat(
        [sheet_1, sheet_2],
        ignore_index=True
    )

    data.columns = data.columns.astype(str).str.strip()

    required_columns = [
        "Invoice",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "Price",
        "Customer ID",
        "Country",
        "Total Price"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns in Excel file: {missing_columns}"
        )

    # Convert columns to correct data types
    data["InvoiceDate"] = pd.to_datetime(
        data["InvoiceDate"],
        errors="coerce"
    )

    for column in ["Quantity", "Price", "Total Price", "Customer ID"]:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    # Remove exact duplicate rows after combining sheets
    data = data.drop_duplicates().copy()

    # Remove rows missing essential reporting information
    data = data.dropna(
        subset=[
            "Invoice",
            "InvoiceDate",
            "Quantity",
            "Price",
            "Total Price",
            "Customer ID",
            "Country"
        ]
    ).copy()

    # Use the dataset's existing revenue column
    data["Revenue"] = data["Total Price"]

    # Date features
    data["Month"] = data["InvoiceDate"].dt.to_period("M").astype(str)
    data["Day of Week"] = data["InvoiceDate"].dt.day_name()
    data["Weekday Number"] = data["InvoiceDate"].dt.dayofweek

    return data


try:
    sales = load_data()
except Exception as error:
    st.error("Unable to load your Excel dataset.")
    st.write(
        "Check that cleaned_online_retail.xlsx is in the same "
        "folder as app.py and that the sheet names are correct."
    )
    st.code(str(error))
    st.stop()


# =====================================================
# 4. SIDEBAR AND FILTERS
# =====================================================
st.sidebar.title("RetailPulse")
st.sidebar.caption("AI-Powered Customer Analytics")

page = st.sidebar.radio(
    "Choose Dashboard",
    [
        "Executive Overview",
        "Sales Analysis",
        "Customer Analytics",
        "Churn Analysis",
        "Demand & Inventory"
    ]
)

# Slicers only on dashboards 3, 4 and 5
if page in [
    "Customer Analytics",
    "Churn Analysis",
    "Demand & Inventory"
]:
    st.sidebar.subheader("Dashboard Filters")

    min_date = sales["InvoiceDate"].min().date()
    max_date = sales["InvoiceDate"].max().date()

    date_range = st.sidebar.date_input(
        "Invoice Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_date, end_date = date_range

        df = sales[
            (sales["InvoiceDate"].dt.date >= start_date)
            & (sales["InvoiceDate"].dt.date <= end_date)
        ].copy()
    else:
        df = sales.copy()
else:
    df = sales.copy()


# =====================================================
# 5. COMMON FUNCTIONS
# =====================================================
def show_kpis(data):
    revenue = data["Revenue"].sum()
    orders = data["Invoice"].nunique()
    customers = data["Customer ID"].nunique()
    units = data["Quantity"].sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Revenue", f"{revenue:,.2f}")
    col2.metric("Total Orders", f"{orders:,.0f}")
    col3.metric("Total Customers", f"{customers:,.0f}")
    col4.metric("Units Sold", f"{units:,.0f}")


def show_no_data(data):
    if data.empty:
        st.warning("No records found for the selected filters.")
        st.stop()


def make_bar(data, x, y, title, horizontal=False):
    if horizontal:
        fig = px.bar(
            data,
            x=x,
            y=y,
            orientation="h",
            title=title
        )
    else:
        fig = px.bar(
            data,
            x=x,
            y=y,
            title=title
        )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=60, b=20)
    )
    return fig


# =====================================================
# DASHBOARD 1: EXECUTIVE OVERVIEW
# =====================================================
if page == "Executive Overview":

    st.title("RetailPulse – Executive Overview")
    st.caption("Overall business performance at a glance")

    show_kpis(df)

    st.subheader("Monthly Revenue Trend")

    monthly_revenue = (
        df.groupby("Month", as_index=False)["Revenue"]
        .sum()
        .sort_values("Month")
    )

    fig = px.line(
        monthly_revenue,
        x="Month",
        y="Revenue",
        markers=True,
        title="Revenue by Month"
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)

    with left:
        st.subheader("Top 10 Countries by Revenue")

        country_revenue = (
            df.groupby("Country", as_index=False)["Revenue"]
            .sum()
            .nlargest(10, "Revenue")
            .sort_values("Revenue")
        )

        fig = make_bar(
            country_revenue,
            "Revenue",
            "Country",
            "Revenue by Country",
            horizontal=True
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Monthly Orders")

        monthly_orders = (
            df.groupby("Month", as_index=False)
            .agg(Orders=("Invoice", "nunique"))
            .sort_values("Month")
        )

        fig = make_bar(
            monthly_orders,
            "Month",
            "Orders",
            "Number of Orders by Month"
        )
        st.plotly_chart(fig, use_container_width=True)


# =====================================================
# DASHBOARD 2: SALES ANALYSIS
# =====================================================
elif page == "Sales Analysis":

    st.title("RetailPulse – Sales Analysis")
    st.caption("Sales trends, products and order patterns")

    show_kpis(df)

    left, right = st.columns(2)

    with left:
        st.subheader("Revenue by Day of Week")

        weekday_revenue = (
            df.groupby(
                ["Weekday Number", "Day of Week"],
                as_index=False
            )["Revenue"]
            .sum()
            .sort_values("Weekday Number")
        )

        fig = make_bar(
            weekday_revenue,
            "Day of Week",
            "Revenue",
            "Revenue by Weekday"
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Orders by Day of Week")

        weekday_orders = (
            df.groupby(
                ["Weekday Number", "Day of Week"],
                as_index=False
            )
            .agg(Orders=("Invoice", "nunique"))
            .sort_values("Weekday Number")
        )

        fig = make_bar(
            weekday_orders,
            "Day of Week",
            "Orders",
            "Orders by Weekday"
        )
        st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)

    with left:
        st.subheader("Top 10 Products by Revenue")

        product_revenue = (
            df.groupby("Description", as_index=False)["Revenue"]
            .sum()
            .nlargest(10, "Revenue")
            .sort_values("Revenue")
        )

        fig = make_bar(
            product_revenue,
            "Revenue",
            "Description",
            "Top Products",
            horizontal=True
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Monthly Revenue Trend")

        monthly = (
            df.groupby("Month", as_index=False)["Revenue"]
            .sum()
            .sort_values("Month")
        )

        fig = px.line(
            monthly,
            x="Month",
            y="Revenue",
            markers=True,
            title="Monthly Revenue"
        )
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 10 Customers by Revenue")

    top_customers = (
        df.groupby("Customer ID", as_index=False)["Revenue"]
        .sum()
        .nlargest(10, "Revenue")
        .copy()
    )

    top_customers["Customer ID"] = (
        top_customers["Customer ID"].astype(int).astype(str)
    )

    fig = make_bar(
        top_customers.sort_values("Revenue"),
        "Revenue",
        "Customer ID",
        "Top Customers",
        horizontal=True
    )
    st.plotly_chart(fig, use_container_width=True)


# =====================================================
# DASHBOARD 3: CUSTOMER ANALYTICS
# =====================================================
elif page == "Customer Analytics":

    st.title("RetailPulse – Customer Analytics")
    show_no_data(df)
    show_kpis(df)

    customer_data = (
        df.groupby("Customer ID")
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("Invoice", "nunique"),
            LastPurchase=("InvoiceDate", "max")
        )
        .reset_index()
    )

    reference_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)

    customer_data["Recency Days"] = (
        reference_date - customer_data["LastPurchase"]
    ).dt.days

    # Simple descriptive segments, not ML-generated segments
    customer_data["Segment"] = "Regular"

    customer_data.loc[
        customer_data["Revenue"] >= customer_data["Revenue"].quantile(0.75),
        "Segment"
    ] = "High Value"

    customer_data.loc[
        customer_data["Orders"] == 1,
        "Segment"
    ] = "One-Time Buyer"

    left, right = st.columns(2)

    with left:
        st.subheader("Customer Segments")

        segment_counts = (
            customer_data["Segment"]
            .value_counts()
            .rename_axis("Segment")
            .reset_index(name="Customers")
        )

        fig = px.pie(
            segment_counts,
            names="Segment",
            values="Customers",
            hole=0.4,
            title="Customers by Segment"
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Revenue by Segment")

        segment_revenue = (
            customer_data.groupby("Segment", as_index=False)["Revenue"]
            .sum()
        )

        fig = make_bar(
            segment_revenue,
            "Segment",
            "Revenue",
            "Revenue by Customer Segment"
        )
        st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)

    with left:
        st.subheader("Customer Recency")

        fig = px.histogram(
            customer_data,
            x="Recency Days",
            nbins=30,
            title="Days Since Last Purchase"
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Purchase Frequency vs Revenue")

        fig = px.scatter(
            customer_data,
            x="Orders",
            y="Revenue",
            color="Segment",
            hover_data=["Customer ID"],
            title="Orders vs Customer Revenue"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 10 Customers")

    top_customers = customer_data.nlargest(10, "Revenue").copy()
    top_customers["Customer ID"] = (
        top_customers["Customer ID"].astype(int).astype(str)
    )

    fig = make_bar(
        top_customers.sort_values("Revenue"),
        "Revenue",
        "Customer ID",
        "Top Customers by Revenue",
        horizontal=True
    )
    st.plotly_chart(fig, use_container_width=True)


# =====================================================
# DASHBOARD 4: CHURN ANALYSIS
# =====================================================
elif page == "Churn Analysis":

    st.title("RetailPulse – Churn Analysis")
    st.caption(
        "Inactivity-based risk estimates, not predictions from a trained ML model."
    )
    show_no_data(df)

    customer_data = (
        df.groupby("Customer ID")
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("Invoice", "nunique"),
            LastPurchase=("InvoiceDate", "max")
        )
        .reset_index()
    )

    reference_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)

    customer_data["Inactive Days"] = (
        reference_date - customer_data["LastPurchase"]
    ).dt.days

    def assign_risk(days):
        if days <= 90:
            return "Low Risk"
        elif days <= 180:
            return "Medium Risk"
        else:
            return "High Risk"

    customer_data["Risk Level"] = (
        customer_data["Inactive Days"].apply(assign_risk)
    )

    total_customers = customer_data["Customer ID"].nunique()
    high_risk = (customer_data["Risk Level"] == "High Risk").sum()
    medium_risk = (customer_data["Risk Level"] == "Medium Risk").sum()

    high_risk_revenue = customer_data.loc[
        customer_data["Risk Level"] == "High Risk",
        "Revenue"
    ].sum()

    a, b, c, d = st.columns(4)

    a.metric("Customers", f"{total_customers:,}")
    b.metric("High Risk Customers", f"{high_risk:,}")
    c.metric("Medium Risk Customers", f"{medium_risk:,}")
    d.metric("High Risk Customer Revenue", f"{high_risk_revenue:,.2f}")

    left, right = st.columns(2)

    with left:
        st.subheader("Customers by Risk Level")

        risk_counts = (
            customer_data["Risk Level"]
            .value_counts()
            .rename_axis("Risk Level")
            .reset_index(name="Customers")
        )

        fig = px.pie(
            risk_counts,
            names="Risk Level",
            values="Customers",
            hole=0.4,
            title="Inactivity Risk Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Inactivity vs Revenue")

        fig = px.scatter(
            customer_data,
            x="Inactive Days",
            y="Revenue",
            color="Risk Level",
            hover_data=["Customer ID", "Orders"],
            title="Customer Inactivity and Revenue"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Customers to Review")

    at_risk = customer_data[
        customer_data["Risk Level"].isin(
            ["High Risk", "Medium Risk"]
        )
    ].sort_values("Inactive Days", ascending=False)

    st.dataframe(at_risk, use_container_width=True)


# =====================================================
# DASHBOARD 5: DEMAND & INVENTORY
# =====================================================
elif page == "Demand & Inventory":

    st.title("RetailPulse – Demand & Inventory")
    st.caption(
        "Sales quantities are used as a demand indicator. "
        "Actual stock levels and supplier lead times are not available."
    )

    show_no_data(df)
    show_kpis(df)

    product_demand = (
        df.groupby(["StockCode", "Description"], as_index=False)
        .agg(
            Units_Sold=("Quantity", "sum"),
            Revenue=("Revenue", "sum"),
            Orders=("Invoice", "nunique")
        )
        .sort_values("Units_Sold", ascending=False)
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Top 10 Products by Units Sold")

        top_demand = (
            product_demand.head(10)
            .sort_values("Units_Sold")
        )

        fig = make_bar(
            top_demand,
            "Units_Sold",
            "Description",
            "Product Demand",
            horizontal=True
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Monthly Units Sold")

        monthly_demand = (
            df.groupby("Month", as_index=False)["Quantity"]
            .sum()
            .sort_values("Month")
        )

        fig = px.line(
            monthly_demand,
            x="Month",
            y="Quantity",
            markers=True,
            title="Monthly Demand Trend"
        )
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top Countries by Units Sold")

    country_demand = (
        df.groupby("Country", as_index=False)["Quantity"]
        .sum()
        .nlargest(10, "Quantity")
        .sort_values("Quantity")
    )

    fig = make_bar(
        country_demand,
        "Quantity",
        "Country",
        "Demand by Country",
        horizontal=True
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Product Demand Table")

    st.dataframe(
        product_demand.head(50),
        use_container_width=True
    )


# =====================================================
# 6. SIDEBAR FOOTER
# =====================================================
st.sidebar.divider()
st.sidebar.caption("RetailPulse | Online Retail II")
st.sidebar.caption(f"Rows loaded: {len(sales):,}")
