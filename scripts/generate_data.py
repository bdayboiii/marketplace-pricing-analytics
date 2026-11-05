import os
import numpy as np
import pandas as pd

from dotenv import load_dotenv
from sqlalchemy import create_engine, URL

# Reproducibility: same random data every time
np.random.seed(42)

# Load database credentials
load_dotenv()

# Create database connection
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME")
)

engine = create_engine(db_url)

# Simulation configuration
START_DATE = pd.Timestamp("2026-01-01")
NUM_CUSTOMERS = 5000
NUM_DRIVERS = 1000
DAYS = 90

CITIES = ["Pune", "Mumbai", "Bengaluru"]
ZONES_PER_CITY = 5


# GENERATE CITIES

cities = pd.DataFrame({
    "city_name": CITIES
})

cities.to_sql(
    "cities",
    engine,
    if_exists="append",
    index=False
)

# Retrieve generated city IDs from PostgreSQL
city_df = pd.read_sql(
    "SELECT city_id, city_name FROM cities",
    engine
)

print("Cities generated:")
print(city_df)


# GENERATE ZONES

zone_records = []

for _, city in city_df.iterrows():

    for i in range(1, ZONES_PER_CITY + 1):

        zone_records.append({
            "city_id": city["city_id"],
            "zone_name": f"{city['city_name']}_Zone_{i}"
        })

zones = pd.DataFrame(zone_records)

zones.to_sql(
    "zones",
    engine,
    if_exists="append",
    index=False
)

# Retrieve generated zone IDs
zone_df = pd.read_sql(
    "SELECT zone_id, city_id, zone_name FROM zones",
    engine
)

print("\nZones generated:")
print(zone_df.head(10))


# GENERATE CUSTOMERS

customer_city_ids = np.random.choice(
    city_df["city_id"],
    size=NUM_CUSTOMERS,
    p=[0.30, 0.40, 0.30]
)

customers = pd.DataFrame({

    "city_id": customer_city_ids,

    "signup_date": (
        START_DATE -
        pd.to_timedelta(
            np.random.randint(1, 365, NUM_CUSTOMERS),
            unit="D"
        )
    ),

    "customer_segment": np.random.choice(
        ["Regular", "Premium", "Occasional"],
        size=NUM_CUSTOMERS,
        p=[0.50, 0.20, 0.30]
    )
})

customers.to_sql(
    "customers",
    engine,
    if_exists="append",
    index=False,
    chunksize=1000
)

print(f"\nGenerated {len(customers)} customers")


# GENERATE DRIVERS

driver_city_ids = np.random.choice(
    city_df["city_id"],
    size=NUM_DRIVERS,
    p=[0.30, 0.40, 0.30]
)

drivers = pd.DataFrame({

    "city_id": driver_city_ids,

    "vehicle_type": np.random.choice(
        ["Bike", "Auto", "Cab"],
        size=NUM_DRIVERS,
        p=[0.30, 0.40, 0.30]
    ),

    "registration_date": (
        START_DATE -
        pd.to_timedelta(
            np.random.randint(1, 365, NUM_DRIVERS),
            unit="D"
        )
    ),

    "driver_status": np.random.choice(
        ["Active", "Inactive"],
        size=NUM_DRIVERS,
        p=[0.90, 0.10]
    )
})

drivers.to_sql(
    "drivers",
    engine,
    if_exists="append",
    index=False,
    chunksize=1000
)

print(f"\nGenerated {len(drivers)} drivers")