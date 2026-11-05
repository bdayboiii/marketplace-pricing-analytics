import pandas as pd
import matplotlib.pyplot as plt

# Load hourly demand data
df = pd.read_csv("data/hourly_demand.csv")

# Plot demand throughout the day
plt.figure(figsize=(12, 6))

plt.plot(
    df["hour"],
    df["total_requests"],
    marker="o"
)

plt.title("Hourly Ride Demand")
plt.xlabel("Hour of Day")
plt.ylabel("Total Ride Requests")
plt.xticks(range(24))
plt.grid(True)

plt.tight_layout()

# Save chart as an image
plt.savefig("data/hourly_demand.png", dpi=150)

print("Chart saved successfully!")