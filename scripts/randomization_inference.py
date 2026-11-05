
import numpy as np
import pandas as pd
from pathlib import Path

# Configuration

DATA_PATH = Path("data/pricing_experiment_observations.csv")
N_PERMUTATIONS = 5000
RANDOM_SEED = 42

# Load and prepare data

df = pd.read_csv(DATA_PATH)

df["observation_time"] = pd.to_datetime(df["observation_time"])
df["date"] = df["observation_time"].dt.date
df["hour"] = df["observation_time"].dt.hour

# Conversion rate for each zone-hour observation
df["conversion_rate"] = np.divide(
    df["ride_requests"],
    df["search_sessions"],
    out=np.zeros(len(df), dtype=float),
    where=df["search_sessions"].to_numpy() > 0
)

# Search sessions are the observation weights
df["weight"] = df["search_sessions"].astype(float)

df["treatment"] = (
    df["experiment_group"] == "Treatment"
).astype(int)

# Create city-date-hour strata

df = df.sort_values(
    ["city_name", "date", "hour", "zone_id"]
).reset_index(drop=True)

group_sizes = df.groupby(
    ["city_name", "date", "hour"]
).size()

# Five zones should exist in every city-date-hour group
if group_sizes.nunique() != 1:
    raise ValueError(
        "Unequal observations across strata. "
        "Check the input dataset."
    )

group_size = int(group_sizes.iloc[0])
n_groups = len(group_sizes)

# Convert data into matrices:
# Rows = city-date-hour groups
# Columns = zones within each group

weights = df["weight"].to_numpy().reshape(
    n_groups, group_size
)

outcomes = df["conversion_rate"].to_numpy().reshape(
    n_groups, group_size
)

treatment = df["treatment"].to_numpy().reshape(
    n_groups, group_size
)

# Weighted outcome mean within each stratum
weight_sum = weights.sum(axis=1)

outcome_mean = np.divide(
    (weights * outcomes).sum(axis=1),
    weight_sum,
    out=np.zeros(n_groups),
    where=weight_sum > 0
)

# Calculate stratified weighted treatment effect

def calculate_effect(treatment_matrix):

    treatment_weighted_mean = np.divide(
        (weights * treatment_matrix).sum(axis=1),
        weight_sum,
        out=np.zeros(n_groups),
        where=weight_sum > 0
    )

    centered_treatment = (
        treatment_matrix
        - treatment_weighted_mean[:, None]
    )

    centered_outcome = (
        outcomes - outcome_mean[:, None]
    )

    numerator = np.sum(
        weights * centered_treatment * centered_outcome
    )

    denominator = np.sum(
        weights * centered_treatment ** 2
    )

    if denominator == 0:
        return np.nan

    return numerator / denominator


observed_effect = calculate_effect(treatment)

# Randomization inference

rng = np.random.default_rng(RANDOM_SEED)

permutation_effects = []

print("Running randomization inference...")
print(f"Permutations: {N_PERMUTATIONS:,}")

for iteration in range(N_PERMUTATIONS):

    # Randomly reorder treatment labels within each stratum.
    # This preserves the original treatment count per stratum.
    random_order = np.argsort(
        rng.random((n_groups, group_size)),
        axis=1
    )

    permuted_treatment = np.take_along_axis(
        treatment,
        random_order,
        axis=1
    )

    effect = calculate_effect(permuted_treatment)

    if not np.isnan(effect):
        permutation_effects.append(effect)

    if (iteration + 1) % 1000 == 0:
        print(
            f"Completed {iteration + 1:,} "
            f"/ {N_PERMUTATIONS:,}"
        )

permutation_effects = np.array(permutation_effects)

# Calculate permutation p-value

extreme_count = np.sum(
    np.abs(permutation_effects)
    >= abs(observed_effect)
)

# Add-one correction prevents a zero estimated p-value
p_value = (
    extreme_count + 1
) / (
    len(permutation_effects) + 1
)

# Save results

results = pd.DataFrame({
    "permutation_effect": permutation_effects
})

results.to_csv(
    "data/randomization_inference_results.csv",
    index=False
)

# Display results

print("\nRANDOMIZATION INFERENCE")

print(f"Observations: {len(df):,}")
print(f"Strata: {n_groups:,}")
print(f"Zones per stratum: {group_size}")
print(f"Permutations completed: {len(permutation_effects):,}")

print("\nRESULTS")

print(
    f"Observed treatment effect: "
    f"{observed_effect * 100:.3f} percentage points"
)

print(
    f"Permutation null mean: "
    f"{permutation_effects.mean() * 100:.3f} pp"
)

print(
    f"Permutation null standard deviation: "
    f"{permutation_effects.std(ddof=1) * 100:.3f} pp"
)

print(f"Two-sided permutation p-value: {p_value:.6f}")

print("\nINTERPRETATION")

if p_value < 0.05:
    print(
        "The observed treatment effect is unusual "
        "under the stratified permutation null."
    )
else:
    print(
        "The observed treatment effect is not unusual "
        "under the stratified permutation null."
    )

print(
    "\nNote: This test assumes treatment labels are "
    "exchangeable within city-date-hour strata."
)

print(
    "It preserves treatment counts within each stratum "
    "and is a robustness check, not proof of causality."
)


import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))

plt.hist(
    permutation_effects * 100,
    bins=50,
    edgecolor="black",
    alpha=0.75
)

plt.axvline(
    observed_effect * 100,
    linestyle="--",
    linewidth=2,
    label=f"Observed effect: {observed_effect * 100:.2f} pp"
)

plt.axvline(
    -observed_effect * 100,
    linestyle=":",
    linewidth=1.5,
    label="Opposite-tail reference"
)

plt.title("Randomization Inference: Null Distribution")
plt.xlabel("Treatment Effect (percentage points)")
plt.ylabel("Number of Permutations")
plt.legend()
plt.grid(axis="y", alpha=0.3)

plt.tight_layout()

plt.savefig(
    "data/randomization_null_distribution.png",
    dpi=150
)

plt.close()

print(
    "\nSaved: data/randomization_null_distribution.png"
)
