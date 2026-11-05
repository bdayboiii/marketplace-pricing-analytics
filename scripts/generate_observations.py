import os
import numpy as np
import pandas as pd

from dotenv import load_dotenv
from sqlalchemy import create_engine, URL

np.random.seed(42)

load_dotenv()

# Connect to PostgreSQL
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME")
)

engine = create_engine(db_url)

START_DATE = pd.Timestamp("2026-01-01")
DAYS = 90

# Fetch cities
cities = pd.read_sql(
    "SELECT * FROM cities",
    engine
)

# Fetch zones
zones = pd.read_sql(
    "SELECT * FROM zones",
    engine
)

# Fetch drivers
drivers = pd.read_sql(
    "SELECT * FROM drivers",
    engine
)

print("Cities:", len(cities))
print("Zones:", len(zones))
print("Drivers:", len(drivers))

def get_peak_multiplier(hour):
    """
    Simulate daily demand patterns.
    Morning and evening commute hours have higher demand.
    """

    if 8 <= hour <= 10:
        return 1.5

    elif 17 <= hour <= 21:
        return 1.8

    elif 12 <= hour <= 14:
        return 1.2

    elif 0 <= hour <= 5:
        return 0.3

    return 0.8


def get_weekend_multiplier(day):
    """
    Weekend demand is slightly higher in this simulation.
    """

    return 1.15 if day >= 5 else 1.0

demand_records = []
supply_records = []

timestamps = pd.date_range(
    start=START_DATE,
    periods=DAYS * 24,
    freq="h"
)

observation_id = 1

# City-specific demand multipliers
city_multipliers = {
    "Pune": 1.0,
    "Mumbai": 1.5,
    "Bengaluru": 1.2
}

for timestamp in timestamps:

    hour = timestamp.hour
    weekday = timestamp.dayofweek

    peak_factor = get_peak_multiplier(hour)
    weekend_factor = get_weekend_multiplier(weekday)

    for _, zone in zones.iterrows():

        city_id = int(zone["city_id"])

        city_name = cities.loc[
            cities["city_id"] == city_id,
            "city_name"
        ].iloc[0]

        city_factor = city_multipliers[city_name]

        # 1. GENERATE DRIVER SUPPLY

        active_drivers = drivers[
            (drivers["city_id"] == city_id) &
            (drivers["driver_status"] == "Active")
        ]

        # Approximate driver population per zone
        zone_driver_pool = len(active_drivers) / 5

        # Available drivers vary over time
        available = int(
            zone_driver_pool *
            np.random.uniform(0.12, 0.25)
        )

        busy = int(
            zone_driver_pool *
            np.random.uniform(0.25, 0.45)
        )

        # Remaining drivers are offline
        offline = max(
            0,
            int(zone_driver_pool) - available - busy
        )

        # 2. GENERATE CUSTOMER SEARCHES

        base_searches = 5

        searches = np.random.poisson(
            base_searches *
            city_factor *
            peak_factor *
            weekend_factor
        )

        searches = max(searches, 1)

        # 3. RANDOMISED PRICING EXPERIMENT

        treatment = np.random.random() < 0.20

        if treatment:
            experiment_group = "Treatment"
            pricing_multiplier = 1.10
        else:
            experiment_group = "Control"
            pricing_multiplier = 1.00

        # 4. SIMULATE CUSTOMER RESPONSE

        price_sensitivity = 1.2

        conversion_probability = (
            0.65 *
            np.exp(
                -price_sensitivity *
                (pricing_multiplier - 1)
            )
        )

        requests = np.random.binomial(
            searches,
            conversion_probability
        )

        # 5. SAVE DEMAND OBSERVATION

        demand_records.append({
            "observation_id": observation_id,
            "zone_id": int(zone["zone_id"]),
            "observation_time": timestamp,
            "search_sessions": searches,
            "ride_requests": requests,
            "average_quoted_fare": round(
                80 * pricing_multiplier, 2
            ),
            "pricing_multiplier": pricing_multiplier,
            "experiment_group": experiment_group
        })

        # 6. SAVE SUPPLY OBSERVATION

        supply_records.append({
            "observation_id": observation_id,
            "zone_id": int(zone["zone_id"]),
            "observation_time": timestamp,
            "available_drivers": available,
            "busy_drivers": busy,
            "offline_drivers": offline
        })

        observation_id += 1


# Convert records into DataFrames
demand = pd.DataFrame(demand_records)
supply = pd.DataFrame(supply_records)

print("Demand observations:", len(demand))
print("Supply observations:", len(supply))

# Store demand observations
demand.to_sql(
    "demand_observations",
    engine,
    if_exists="append",
    index=False,
    chunksize=1000
)

# Store supply observations
supply.to_sql(
    "supply_observations",
    engine,
    if_exists="append",
    index=False,
    chunksize=1000
)

print("Demand and supply data successfully loaded!")