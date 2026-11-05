
import pandas as pd
import statsmodels.formula.api as smf

# LOAD DATA

df = pd.read_csv(
    "data/pricing_experiment_observations.csv"
)

df["observation_time"] = pd.to_datetime(
    df["observation_time"]
)

df["observation_date"] = (
    df["observation_time"].dt.date.astype(str)
)

df["hour"] = df["observation_time"].dt.hour

# Keep observations with at least one search
df = df[df["search_sessions"] > 0].copy()

# PREPARE VARIABLES

df["conversion_rate"] = (
    df["ride_requests"] / df["search_sessions"]
)

df["treatment"] = (
    df["experiment_group"] == "Treatment"
).astype(int)

# WEIGHTED LEAST SQUARES REGRESSION

model = smf.wls(
    formula="""
        conversion_rate ~ treatment
        + C(city_name)
        + C(hour)
        + C(observation_date)
    """,
    data=df,
    weights=df["search_sessions"]
)

# Cluster standard errors by zone.
# This accounts for repeated observations within zones.

results = model.fit(
    cov_type="cluster",
    cov_kwds={
        "groups": df["zone_id"],
        "use_correction": True
    },
    use_t=True
)

# EXTRACT RESULTS

coefficient = results.params["treatment"]
confidence_interval = results.conf_int().loc["treatment"]

p_value = results.pvalues["treatment"]
standard_error = results.bse["treatment"]

# Convert conversion-rate units to percentage points
effect_pp = coefficient * 100
ci_lower_pp = confidence_interval.iloc[0] * 100
ci_upper_pp = confidence_interval.iloc[1] * 100
se_pp = standard_error * 100

# PRINT RESULTS

print("\n========== CLUSTERED PRICING REGRESSION ==========")

print(f"Observations: {len(df):,}")
print(f"Zones (clusters): {df['zone_id'].nunique()}")
print(f"Cities: {df['city_name'].nunique()}")
print(f"Dates: {df['observation_date'].nunique()}")

print("\nModel: Weighted Least Squares")
print("Controls: City, hour and date fixed effects")
print("Standard errors: Clustered by zone")
print("Weights: Search sessions")

print("\n---------------- TREATMENT EFFECT ----------------")

print(
    f"Treatment effect: {effect_pp:.3f} percentage points"
)

print(
    f"Clustered standard error: {se_pp:.3f} percentage points"
)

print(
    f"95% confidence interval: "
    f"[{ci_lower_pp:.3f}, {ci_upper_pp:.3f}] pp"
)

print(f"P-value: {p_value:.6g}")

print(f"R-squared: {results.rsquared:.4f}")

print("\n---------------- INTERPRETATION ----------------")

if p_value < 0.05:
    print(
        "The treatment effect is statistically significant "
        "at the 5% level under this model."
    )
else:
    print(
        "The treatment effect is not statistically significant "
        "at the 5% level under this model."
    )

if coefficient < 0:
    print(
        "The 10% pricing increase is associated with "
        "a reduction in conversion."
    )
else:
    print(
        "The 10% pricing increase is associated with "
        "an increase in conversion."
    )

print(
    "\nWARNING: Only 15 zone clusters are available. "
    "Cluster-robust inference with so few clusters "
    "can be unreliable. Treat the p-value and confidence "
    "interval as provisional."
)

print("\n==================================================")
