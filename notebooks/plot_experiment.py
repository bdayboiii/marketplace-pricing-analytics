
import pandas as pd
import matplotlib.pyplot as plt

# Load corrected city-level revenue data
revenue = pd.read_csv("data/city_revenue.csv")

# Load experiment observations
experiment = pd.read_csv(
    "data/pricing_experiment_observations.csv"
)

# Chart 1: Revenue per search by city

pivot = revenue.pivot(
    index="city_name",
    columns="experiment_group",
    values="revenue_per_search"
)

ax = pivot.plot(
    kind="bar",
    figsize=(9, 5),
    width=0.7
)

ax.set_title("Revenue per Search by City")
ax.set_xlabel("City")
ax.set_ylabel("Revenue per Search (INR)")
ax.legend(title="Experiment Group")
ax.grid(axis="y", alpha=0.3)

plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("data/revenue_per_search.png", dpi=150)
plt.close()


# Chart 2: Weighted conversion rate

conversion = (
    experiment.groupby("experiment_group")
    .agg(
        total_searches=("search_sessions", "sum"),
        total_requests=("ride_requests", "sum")
    )
)

conversion["conversion_rate"] = (
    conversion["total_requests"] /
    conversion["total_searches"] * 100
)

conversion = conversion.reindex(["Control", "Treatment"])

ax = conversion["conversion_rate"].plot(
    kind="bar",
    figsize=(7, 5),
    width=0.5
)

ax.set_title("Weighted Conversion Rate by Experiment Group")
ax.set_xlabel("Experiment Group")
ax.set_ylabel("Conversion Rate (%)")
ax.grid(axis="y", alpha=0.3)

plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("data/pricing_conversion.png", dpi=150)
plt.close()

print("Updated charts:")
print("- data/revenue_per_search.png")
print("- data/pricing_conversion.png")

print("\nWeighted conversion rates:")
print(conversion["conversion_rate"].round(2))
