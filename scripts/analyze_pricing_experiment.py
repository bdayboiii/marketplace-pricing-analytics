
import pandas as pd
import numpy as np
from scipy import stats

# Load observation-level experiment data
df = pd.read_csv("data/pricing_experiment_observations.csv")

# Calculate conversion for each zone-hour observation
df["conversion_rate"] = (
    df["ride_requests"] / df["search_sessions"]
)

control = df.loc[
    df["experiment_group"] == "Control", "conversion_rate"
].dropna()

treatment = df.loc[
    df["experiment_group"] == "Treatment", "conversion_rate"
].dropna()

# Group statistics
control_mean = control.mean()
treatment_mean = treatment.mean()

difference = treatment_mean - control_mean

# Welch's independent two-sample t-test
test = stats.ttest_ind(
    treatment,
    control,
    equal_var=False
)

# Welch confidence interval for difference in means
n_control = len(control)
n_treatment = len(treatment)

se = np.sqrt(
    control.var(ddof=1) / n_control
    + treatment.var(ddof=1) / n_treatment
)

df_num = (
    control.var(ddof=1) / n_control
    + treatment.var(ddof=1) / n_treatment
) ** 2

df_den = (
    (control.var(ddof=1) / n_control) ** 2 / (n_control - 1)
    + (treatment.var(ddof=1) / n_treatment) ** 2 / (n_treatment - 1)
)

degrees_of_freedom = df_num / df_den

critical_value = stats.t.ppf(
    0.975, degrees_of_freedom
)

ci_lower = difference - critical_value * se
ci_upper = difference + critical_value * se

# Print results
print("\n===== PRICING EXPERIMENT STATISTICAL ANALYSIS =====")

print(f"Control observations: {n_control}")
print(f"Treatment observations: {n_treatment}")

print(f"\nControl mean conversion: {control_mean * 100:.2f}%")
print(f"Treatment mean conversion: {treatment_mean * 100:.2f}%")

print(
    f"Difference (Treatment - Control): "
    f"{difference * 100:.2f} percentage points"
)

print(f"\nWelch t-statistic: {test.statistic:.4f}")
print(f"P-value: {test.pvalue:.6g}")

print(
    f"95% confidence interval: "
    f"[{ci_lower * 100:.2f}, {ci_upper * 100:.2f}] "
    "percentage points"
)

if test.pvalue < 0.05:
    print("\nResult: Statistically significant at the 5% level.")
else:
    print("\nResult: Not statistically significant at the 5% level.")
