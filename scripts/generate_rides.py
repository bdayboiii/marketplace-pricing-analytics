import os
import numpy as np
import pandas as pd

from dotenv import load_dotenv
from sqlalchemy import create_engine, URL

np.random.seed(42)

load_dotenv()

db_url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME")
)

engine = create_engine(db_url)

# Fetch existing marketplace data
customers = pd.read_sql("SELECT * FROM customers", engine)
drivers = pd.read_sql("SELECT * FROM drivers", engine)
zones = pd.read_sql("SELECT * FROM zones", engine)

demand = pd.read_sql(
    "SELECT * FROM demand_observations ORDER BY observation_id",
    engine
)

supply = pd.read_sql(
    "SELECT * FROM supply_observations ORDER BY observation_id",
    engine
)

# Map each zone to its city
zone_city = zones.set_index("zone_id")["city_id"].to_dict()

# Map supply observations to their available driver counts
supply_map = supply.set_index("observation_id")[
    "available_drivers"
].to_dict()

# Pre-group customers and drivers by city
customers_by_city = {
    city_id: group["customer_id"].to_numpy()
    for city_id, group in customers.groupby("city_id")
}

drivers_by_city_vehicle = {
    (city_id, vehicle): group["driver_id"].to_numpy()
    for (city_id, vehicle), group
    in drivers[drivers["driver_status"] == "Active"].groupby(
        ["city_id", "vehicle_type"]
    )
}

def calculate_base_fare(vehicle, distance):
    """Calculate estimated fare before surge pricing."""

    base_fares = {
        "Bike": 25,
        "Auto": 40,
        "Cab": 70
    }

    return base_fares[vehicle] + distance * 12

ride_records = []

ride_id = 1

VEHICLES = ["Bike", "Auto", "Cab"]
VEHICLE_PROBS = [0.30, 0.40, 0.30]

for _, observation in demand.iterrows():

    zone_id = int(observation["zone_id"])
    city_id = int(zone_city[zone_id])

    requests = int(observation["ride_requests"])

    if requests == 0:
        continue

    available = supply_map[
        int(observation["observation_id"])
    ]

    # Generate each requested ride
    for _ in range(requests):

        # Select a customer from the same city
        customer_id = np.random.choice(
            customers_by_city[city_id]
        )

        # Select vehicle category
        vehicle = np.random.choice(
            VEHICLES,
            p=VEHICLE_PROBS
        )

        # Select drop zone from the same city
        city_zones = zones[
            zones["city_id"] == city_id
        ]["zone_id"].to_numpy()

        drop_zone_id = np.random.choice(city_zones)

        # Simulate ride distance
        distance = np.random.uniform(1, 20)

        # Calculate fare
        base_fare = calculate_base_fare(
            vehicle,
            distance
        )

        surge = float(observation["pricing_multiplier"])

        estimated_fare = base_fare * surge

        # ---------------------------------
        # DRIVER ASSIGNMENT
        # ---------------------------------

        # Higher demand relative to available drivers
        # reduces the probability of getting a driver.

        supply_ratio = available / max(requests, 1)

        fulfilment_probability = min(
            0.95,
            0.55 + 0.40 * min(supply_ratio, 1)
        )

        assigned = (
            np.random.random() < fulfilment_probability
        )

        driver_id = None
        wait_time = None

        if assigned:

            eligible_drivers = drivers_by_city_vehicle.get(
                (city_id, vehicle),
                np.array([])
            )

            if len(eligible_drivers) == 0:
                assigned = False
            else:
                driver_id = int(
                    np.random.choice(eligible_drivers)
                )

        # RIDE OUTCOME

        if not assigned:

            status = "Unfulfilled"

        else:

            wait_time = np.random.uniform(
                3,
                8 + 4 * requests / max(available, 1)
            )

            cancellation_probability = min(
                0.65,
                0.05 + wait_time / 60
            )

            if np.random.random() < cancellation_probability:
                status = "Customer_Cancelled"

            elif np.random.random() < 0.05:
                status = "Driver_Cancelled"

            else:
                status = "Completed"

        # FINAL FARE AND DURATION

        final_fare = (
            round(estimated_fare, 2)
            if status == "Completed"
            else None
        )

        duration = (
            round(distance * np.random.uniform(3, 5), 2)
            if status == "Completed"
            else None
        )

        ride_records.append({
            "ride_id": ride_id,
            "customer_id": int(customer_id),
            "driver_id": driver_id,
            "city_id": city_id,
            "pickup_zone_id": zone_id,
            "drop_zone_id": int(drop_zone_id),
            "request_time": observation["observation_time"],
            "ride_status": status,
            "vehicle_type": vehicle,
            "distance_km": round(distance, 2),
            "estimated_fare": round(estimated_fare, 2),
            "final_fare": final_fare,
            "surge_multiplier": surge,
            "wait_time_minutes": (
                round(wait_time, 2)
                if wait_time is not None
                else None
            ),
            "duration_minutes": duration
        })

        ride_id += 1


rides = pd.DataFrame(ride_records)

print("Total rides generated:", len(rides))
print(rides.head())

rides.to_sql(
    "rides",
    engine,
    if_exists="append",
    index=False,
    chunksize=1000
)

print("Ride transactions successfully loaded!")