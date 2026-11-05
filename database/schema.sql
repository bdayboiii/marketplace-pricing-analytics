
-- MARKETPLACE ANALYTICS DATABASE

-- 1. Cities
CREATE TABLE cities (
    city_id SERIAL PRIMARY KEY,
    city_name VARCHAR(50) UNIQUE NOT NULL
);

-- 2. Geographical zones
CREATE TABLE zones (
    zone_id SERIAL PRIMARY KEY,
    city_id INT REFERENCES cities(city_id),
    zone_name VARCHAR(100) NOT NULL,
    UNIQUE(city_id, zone_name)
);

-- 3. Customers
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    city_id INT REFERENCES cities(city_id),
    signup_date DATE NOT NULL,
    customer_segment VARCHAR(30)
);

-- 4. Drivers
CREATE TABLE drivers (
    driver_id SERIAL PRIMARY KEY,
    city_id INT REFERENCES cities(city_id),
    vehicle_type VARCHAR(20),
    registration_date DATE NOT NULL,
    driver_status VARCHAR(20) DEFAULT 'Active'
);

-- 5. Rides
CREATE TABLE rides (
    ride_id BIGINT PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    driver_id INT REFERENCES drivers(driver_id),
    city_id INT REFERENCES cities(city_id),
    pickup_zone_id INT REFERENCES zones(zone_id),
    drop_zone_id INT REFERENCES zones(zone_id),

    request_time TIMESTAMP NOT NULL,
    ride_status VARCHAR(30) NOT NULL,

    vehicle_type VARCHAR(20),
    distance_km NUMERIC(8,2),

    estimated_fare NUMERIC(10,2),
    final_fare NUMERIC(10,2),
    surge_multiplier NUMERIC(4,2),

    wait_time_minutes NUMERIC(8,2),
    duration_minutes NUMERIC(8,2)
);

-- 6. Demand observations
CREATE TABLE demand_observations (
    observation_id BIGINT PRIMARY KEY,
    zone_id INT REFERENCES zones(zone_id),
    observation_time TIMESTAMP NOT NULL,

    search_sessions INT NOT NULL,
    ride_requests INT NOT NULL,

    average_quoted_fare NUMERIC(10,2),
    pricing_multiplier NUMERIC(4,2),
    experiment_group VARCHAR(20)
);

-- 7. Supply observations
CREATE TABLE supply_observations (
    observation_id BIGINT PRIMARY KEY,
    zone_id INT REFERENCES zones(zone_id),
    observation_time TIMESTAMP NOT NULL,

    available_drivers INT NOT NULL,
    busy_drivers INT NOT NULL,
    offline_drivers INT NOT NULL
);

-- 8. Pricing experiments
CREATE TABLE pricing_experiments (
    experiment_id SERIAL PRIMARY KEY,
    experiment_name VARCHAR(100),
    zone_id INT REFERENCES zones(zone_id),

    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,

    experiment_group VARCHAR(20),
    pricing_multiplier NUMERIC(4,2)
);

-- INDEXES

CREATE INDEX idx_rides_time
ON rides(request_time);

CREATE INDEX idx_rides_city
ON rides(city_id);

CREATE INDEX idx_rides_status
ON rides(ride_status);

CREATE INDEX idx_demand_zone_time
ON demand_observations(zone_id, observation_time);

CREATE INDEX idx_supply_zone_time
ON supply_observations(zone_id, observation_time);
