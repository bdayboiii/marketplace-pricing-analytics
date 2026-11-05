import os
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import numpy as np
from scipy import stats
import statsmodels.formula.api as smf

# PAGE CONFIGURATION

st.set_page_config(
    page_title="Marketplace Pricing Analytics",
    page_icon="🚕",
    layout="wide"
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

st.title("Marketplace Pricing & Demand Analytics")
st.caption(
    "Synthetic ride-hailing marketplace | "
    "Pune, Mumbai and Bengaluru"
)

# LOAD DATA

@st.cache_data
def load_data():
    hourly = pd.read_csv(DATA / "city_hourly_metrics.csv")
    revenue = pd.read_csv(DATA / "city_revenue.csv")
    experiment = pd.read_csv(
        DATA / "pricing_experiment_observations.csv"
    )
    outcomes = pd.read_csv(DATA / "city_ride_outcomes.csv")

    return hourly, revenue, experiment, outcomes


try:
    hourly, revenue, experiment, outcomes = load_data()
except (FileNotFoundError, KeyError) as error:
    st.error(f"Data loading error: {error}")
    st.stop()

# CITY FILTER

st.sidebar.header("Dashboard Filters")

cities = sorted(experiment["city_name"].unique())

selected_cities = st.sidebar.multiselect(
    "Select cities",
    cities,
    default=cities
)

if not selected_cities:
    st.warning("Please select at least one city.")
    st.stop()

hourly_filtered = hourly[
    hourly["city_name"].isin(selected_cities)
].copy()

revenue_filtered = revenue[
    revenue["city_name"].isin(selected_cities)
].copy()

experiment_filtered = experiment[
    experiment["city_name"].isin(selected_cities)
].copy()

outcomes_filtered = outcomes[
    outcomes["city_name"].isin(selected_cities)
].copy()

# KPI CALCULATIONS

total_searches = int(
    experiment_filtered["search_sessions"].sum()
)

total_requests = int(
    experiment_filtered["ride_requests"].sum()
)

conversion_rate = (
    100 * total_requests / total_searches
    if total_searches else 0
)

total_revenue = revenue_filtered["actual_revenue"].sum()

revenue_per_search = (
    total_revenue / total_searches
    if total_searches else 0
)


# MARKETPLACE OVERVIEW

st.subheader("Marketplace Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Searches", f"{total_searches:,}")
col2.metric("Ride Requests", f"{total_requests:,}")
col3.metric("Conversion Rate", f"{conversion_rate:.2f}%")
col4.metric("Actual Revenue", f"₹{total_revenue:,.0f}")

st.metric(
    "Revenue per Search",
    f"₹{revenue_per_search:.2f}"
)

# HOURLY DEMAND

st.divider()
st.subheader("Demand Analysis")

hourly_summary = (
    hourly_filtered.groupby("hour", as_index=False)
    .agg(
        total_searches=("total_searches", "sum"),
        total_requests=("total_requests", "sum"),
        available_drivers=("available_drivers", "sum")
    )
    .sort_values("hour")
)

fig_demand = px.line(
    hourly_summary,
    x="hour",
    y=["total_searches", "total_requests"],
    markers=True,
    title="Hourly Searches vs Ride Requests",
    labels={
        "hour": "Hour of Day",
        "value": "Volume",
        "variable": "Metric"
    }
)

fig_demand.update_layout(
    hovermode="x unified"
)

st.plotly_chart(fig_demand, use_container_width=True)


# DEMAND-SUPPLY ANALYSIS

st.subheader("Demand-Supply Analysis")

# Recalculate the ratio after aggregation.
# Never average city-level ratios directly.

hourly_summary["demand_supply_ratio"] = (
    hourly_summary["total_requests"] /
    hourly_summary["available_drivers"].replace(0, float("nan"))
)

fig_supply = px.line(
    hourly_summary,
    x="hour",
    y="demand_supply_ratio",
    markers=True,
    title="Hourly Demand-to-Supply Ratio",
    labels={
        "hour": "Hour of Day",
        "demand_supply_ratio": "Requests / Available Drivers"
    }
)

fig_supply.update_layout(
    hovermode="x unified"
)

st.plotly_chart(fig_supply, use_container_width=True)

st.caption(
    "Supply is simulated independently of demand. "
    "This ratio is descriptive and does not establish "
    "actual driver shortages."
)


# PRICING EXPERIMENT

st.divider()
st.subheader("Pricing Experiment")

experiment_summary = (
    experiment_filtered.groupby(
        "experiment_group",
        as_index=False
    )
    .agg(
        searches=("search_sessions", "sum"),
        requests=("ride_requests", "sum")
    )
)

experiment_summary["conversion_rate"] = (
    100 * experiment_summary["requests"] /
    experiment_summary["searches"]
)

fig_conversion = px.bar(
    experiment_summary,
    x="experiment_group",
    y="conversion_rate",
    color="experiment_group",
    text_auto=".2f",
    title="Weighted Conversion Rate by Pricing Group",
    labels={
        "experiment_group": "Experiment Group",
        "conversion_rate": "Conversion Rate (%)"
    },
    category_orders={
        "experiment_group": ["Control", "Treatment"]
    }
)

fig_conversion.update_layout(
    showlegend=False,
    yaxis_range=[0, 75]
)

st.plotly_chart(fig_conversion, use_container_width=True)


# EXPERIMENT IMPACT METRICS

group_rates = experiment_summary.set_index(
    "experiment_group"
)["conversion_rate"]

if {"Control", "Treatment"}.issubset(group_rates.index):
    control_rate = group_rates["Control"]
    treatment_rate = group_rates["Treatment"]

    absolute_change = treatment_rate - control_rate

    relative_change = (
        100 * absolute_change / control_rate
        if control_rate else 0
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Control Conversion",
        f"{control_rate:.2f}%"
    )

    col2.metric(
        "Treatment Conversion",
        f"{treatment_rate:.2f}%"
    )

    col3.metric(
        "Conversion Difference",
        f"{absolute_change:+.2f} pp",
        f"{relative_change:+.2f}% relative",
        delta_color="normal"
    )


# CLUSTERED PRICING EXPERIMENT REGRESSION

st.subheader("Statistical Analysis — Clustered Regression")

test_data = experiment_filtered[
    experiment_filtered["search_sessions"] > 0
].copy()

test_data["conversion_rate"] = (
    test_data["ride_requests"] /
    test_data["search_sessions"]
)

test_data["treatment"] = (
    test_data["experiment_group"] == "Treatment"
).astype(int)

test_data["observation_time"] = pd.to_datetime(
    test_data["observation_time"]
)

test_data["observation_date"] = (
    test_data["observation_time"].dt.strftime("%Y-%m-%d")
)

test_data["hour"] = test_data["observation_time"].dt.hour

number_of_clusters = test_data["zone_id"].nunique()

if (
    test_data["experiment_group"].nunique() == 2
    and number_of_clusters >= 2
):

    model = smf.wls(
        formula="""
            conversion_rate ~ treatment
            + C(city_name)
            + C(hour)
            + C(observation_date)
        """,
        data=test_data,
        weights=test_data["search_sessions"]
    )

    results = model.fit(
        cov_type="cluster",
        cov_kwds={
            "groups": test_data["zone_id"],
            "use_correction": True
        },
        use_t=True
    )

    effect = results.params["treatment"] * 100
    standard_error = results.bse["treatment"] * 100
    p_value = results.pvalues["treatment"]

    confidence_interval = results.conf_int().loc["treatment"]

    ci_lower = confidence_interval.iloc[0] * 100
    ci_upper = confidence_interval.iloc[1] * 100

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Treatment Effect",
        f"{effect:+.2f} pp"
    )

    col2.metric(
        "Clustered Standard Error",
        f"{standard_error:.3f} pp"
    )

    col3.metric(
        "P-value",
        f"{p_value:.3e}"
    )

    st.write(
        f"**95% Confidence Interval:** "
        f"[{ci_lower:.2f}, {ci_upper:.2f}] percentage points"
    )

    st.write(
        f"**R-squared:** {results.rsquared:.4f}"
    )

    st.write(
        f"**Observations:** {len(test_data):,}"
    )

    st.write(
        f"**Zone clusters:** {number_of_clusters}"
    )

    if p_value < 0.05:
        st.success(
            "The estimated treatment effect is statistically "
            "significant under the clustered regression model."
        )
    else:
        st.info(
            "The estimated treatment effect is not statistically "
            "significant at the 5% level."
        )

    if number_of_clusters < 30:
        st.warning(
            f"Only {number_of_clusters} zone clusters are included. "
            "Cluster-robust inference may be unreliable with so few "
            "clusters. Treat the p-value and confidence interval "
            "as provisional, especially for individual-city filters."
        )

    with st.expander("Regression methodology"):
        st.markdown(
            """
            **Model:** Weighted Least Squares (WLS)

            - Dependent variable: zone-hour conversion rate
            - Independent variable: treatment indicator
            - Weight: number of search sessions
            - Fixed effects: city, hour of day and calendar date
            - Standard errors: clustered by zone
            - Confidence level: 95%

            **Limitation:** Only 15 zones exist in the full dataset.
            Filtering to a single city leaves only five clusters.
            Conventional cluster-robust inference is therefore
            provisional and should not be interpreted as definitive
            causal evidence.
            """
        )

else:
    st.warning(
        "Both experiment groups and at least two zones are "
        "required for this regression."
    )

# Randomization Inference

st.divider()

st.subheader("Randomization Inference")

st.markdown(
    """
    This analysis tests whether the observed pricing effect
    could plausibly arise from randomly assigning treatment
    labels within city-date-hour groups.
    """
)

# Display permutation distribution
permutation_chart = (
    "data/randomization_null_distribution.png"
)

if os.path.exists(permutation_chart):
    st.image(
        permutation_chart,
        caption="Null distribution from 5,000 stratified permutations",
        use_container_width=True
    )
else:
    st.warning(
        "Permutation distribution chart not found. "
        "Run scripts/randomization_inference.py first."
    )

# Display key metrics
col1, col2, col3 = st.columns(3)

col1.metric(
    "Observed Treatment Effect",
    "-7.69 pp"
)

col2.metric(
    "Permutation p-value",
    "0.000200"
)

col3.metric(
    "Permutations",
    "5,000"
)

st.info(
    """
    Interpretation: The observed treatment effect is far
    outside the permutation null distribution. This supports
    the conclusion that the 10% pricing increase reduced
    conversion under the simulated experiment.

    The test assumes treatment labels are exchangeable within
    city-date-hour strata. It is a robustness check, not proof
    of causality.
    """
)

# CITY-LEVEL REVENUE

st.divider()
st.subheader("Revenue Performance by City")

fig_revenue = px.bar(
    revenue_filtered,
    x="city_name",
    y="revenue_per_search",
    color="experiment_group",
    barmode="group",
    text_auto=".2f",
    title="Revenue per Search by City",
    labels={
        "city_name": "City",
        "revenue_per_search": "Revenue per Search (₹)",
        "experiment_group": "Pricing Group"
    },
    category_orders={
        "experiment_group": ["Control", "Treatment"]
    }
)

st.plotly_chart(fig_revenue, use_container_width=True)

# RIDE OUTCOME ANALYSIS

st.divider()
st.subheader("Ride Outcome Analysis")

outcome_columns = {
    "completed_rides": "Completed",
    "customer_cancellations": "Customer Cancelled",
    "driver_cancellations": "Driver Cancelled",
    "unfulfilled_requests": "Unfulfilled"
}

# Convert counts into percentages
for column in outcome_columns:
    outcomes_filtered[column + "_rate"] = (
        100 * outcomes_filtered[column] /
        outcomes_filtered["total_ride_records"].replace(0, float("nan"))
    )

# Reshape data for Plotly
outcome_rate_columns = [
    column + "_rate" for column in outcome_columns
]

outcome_chart_data = outcomes_filtered.melt(
    id_vars=["city_name", "experiment_group"],
    value_vars=outcome_rate_columns,
    var_name="outcome",
    value_name="percentage"
)

outcome_chart_data["outcome"] = (
    outcome_chart_data["outcome"]
    .str.replace("_rate", "", regex=False)
    .map(outcome_columns)
)

fig_outcomes = px.bar(
    outcome_chart_data,
    x="city_name",
    y="percentage",
    color="outcome",
    facet_col="experiment_group",
    barmode="stack",
    text_auto=".1f",
    title="Distribution of Ride Outcomes by City",
    labels={
        "city_name": "City",
        "percentage": "Percentage of Ride Records (%)",
        "outcome": "Ride Outcome",
        "experiment_group": "Pricing Group"
    },
    category_orders={
        "experiment_group": ["Control", "Treatment"],
        "outcome": [
            "Completed",
            "Customer Cancelled",
            "Driver Cancelled",
            "Unfulfilled"
        ]
    }
)

fig_outcomes.update_layout(
    yaxis_range=[0, 100],
    yaxis_title="Percentage (%)",
    legend_title="Ride Outcome"
)

st.plotly_chart(
    fig_outcomes,
    use_container_width=True
)

# CITY COMPARISON TABLE

st.subheader("City-Level Pricing Comparison")

city_table = revenue_filtered.pivot(
    index="city_name",
    columns="experiment_group",
    values="revenue_per_search"
)

if {"Control", "Treatment"}.issubset(city_table.columns):
    city_table["Change (%)"] = (
        100 * (
            city_table["Treatment"] - city_table["Control"]
        ) / city_table["Control"]
    )

st.dataframe(
    city_table.round(2),
    use_container_width=True
)


# BUSINESS FINDINGS

st.divider()
st.subheader("Business Interpretation")

if {"Control", "Treatment"}.issubset(group_rates.index):
    st.write(
        f"The selected cities show a conversion change of "
        f"**{absolute_change:+.2f} percentage points** "
        f"under the 10% pricing increase."
    )

    revenue_comparison = revenue_filtered.pivot(
        index="city_name",
        columns="experiment_group",
        values="revenue_per_search"
    )

    if {"Control", "Treatment"}.issubset(
        revenue_comparison.columns
    ):
        declines = (
            revenue_comparison["Treatment"] <
            revenue_comparison["Control"]
        )

        if declines.all():
            st.write(
                "Revenue per search is lower under treatment "
                "in every selected city."
            )
        else:
            st.write(
                "The revenue impact varies across the "
                "selected cities."
            )

st.info(
    "Business recommendation: Avoid a blanket 10% "
    "pricing increase under the simulated conditions. "
    "Test smaller price changes and evaluate their "
    "effects on conversion and revenue."
)

with st.expander("Methodology and Limitations"):
    st.markdown(
        """
        - Data is synthetically generated for three cities.
        - Control uses a 1.00 pricing multiplier.
        - Treatment uses a 1.10 pricing multiplier.
        - Conversion is calculated as requests divided by searches.
        - Revenue is based on final fares from completed rides.
        - Revenue per search is actual revenue divided by searches.
        - Experiment assignment occurs at the zone-hour level.
        - Repeated observations may be correlated.
        - Driver supply was simulated independently of demand.
        - Findings demonstrate analytical methodology rather
          than real-world causal evidence.
        """
    )
