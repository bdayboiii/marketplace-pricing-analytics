import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/hourly_imbalance.csv")

plt.figure(figsize=(12, 6))

plt.plot(
    df["hour"],
    df["demand_supply_ratio"],
    marker="o"
)

plt.axhline(
    y=0.5,
    linestyle="--",
    label="Reference ratio (0.5)"
)

plt.title("Hourly Demand-Supply Ratio")
plt.xlabel("Hour of Day")
plt.ylabel("Demand-Supply Ratio")
plt.xticks(range(24))
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("data/hourly_imbalance.png", dpi=300, bbox_inches="tight")
print("Graph saved successfully!")