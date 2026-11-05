# Marketplace Pricing & Demand Analytics

An end-to-end data analytics project investigating demand patterns, marketplace supply, and the impact of dynamic pricing on ride-hailing conversion and revenue.

The project uses synthetic ride-hailing data across Pune, Mumbai, and Bengaluru to simulate marketplace operations and evaluate a 10% pricing increase through SQL analysis, statistical modelling, and an interactive Streamlit dashboard.

## Business Problem

Ride-hailing platforms must balance pricing, customer conversion, revenue, and driver availability.

This project investigates:

- When and where ride demand is highest.
- How demand varies across cities and zones.
- How demand compares with available driver supply.
- Whether a 10% pricing increase improves revenue performance.
- Whether changes in conversion are statistically distinguishable from random assignment variation.

## Key Findings

- Analysed 32,400 zone-hour observations across 3 cities and 15 zones over 90 days.
- Observed an overall weighted conversion rate of approximately 63.54%.
- The treatment group experienced a conversion rate of 57.53%, compared with 65.05% in the control group.
- The estimated treatment effect was approximately -7.54 percentage points in a weighted regression with city, hour, and date fixed effects.
- Stratified randomization inference using 5,000 permutations produced an estimated effect of -7.69 percentage points and a permutation p-value of 0.0002.
- Revenue per search decreased under treatment in all three cities.

**Business recommendation:** Avoid applying a blanket 10% price increase under the simulated conditions. Test smaller pricing changes and evaluate their effects on conversion and revenue.

## Technology Stack

- **Database:** PostgreSQL
- **Languages:** Python, SQL
- **Data analysis:** Pandas, NumPy
- **Statistical analysis:** Statsmodels, SciPy
- **Visualisation:** Matplotlib, Seaborn, Plotly
- **Dashboard:** Streamlit
- **Environment:** Jupyter Notebook, Python virtual environment

## Project Structure

```text
marketplace-pricing-analytics/
├── analysis/
│   ├── demand_analysis.sql
│   ├── pricing_experiment.sql
│   ├── revenue_analysis.sql
│   └── zone_analysis.sql
├── dashboard/
│   └── app.py
├── data/
│   ├── generated CSV files
│   └── analysis charts
├── database/
│   └── schema.sql
├── notebooks/
│   ├── plot_demand.py
│   ├── plot_imbalance.py
│   └── plot_experiment.py
├── scripts/
│   ├── generate_data.py
│   ├── generate_observations.py
│   ├── generate_rides.py
│   ├── clustered_pricing_analysis.py
│   └── randomization_inference.py
├── .env
├── .gitignore
└── README.md
```

## Statistical Methodology

### 1. Descriptive Analysis

SQL queries examine demand by city, hour, weekday, and zone. Additional analysis compares ride outcomes, revenue, and demand-to-supply ratios.

### 2. Pricing Experiment

Observations are assigned to:

- Control: 1.00 pricing multiplier.
- Treatment: 1.10 pricing multiplier.

Conversion is calculated as ride requests divided by search sessions. Revenue per search is calculated using completed-ride revenue divided by searches.

### 3. Clustered Regression

Weighted Least Squares regression estimates the treatment effect while controlling for city, hour, and date fixed effects. Search sessions are used as weights, and standard errors are clustered by zone.

The model uses 15 zone clusters, so its cluster-robust confidence intervals and p-values should be interpreted cautiously.

### 4. Randomization Inference

A stratified permutation test performs 5,000 permutations while preserving treatment counts within city-date-hour strata.

This provides a robustness check under the assumption that treatment labels are exchangeable within those strata.

## Limitations

- All data is synthetically generated and does not represent actual ride-hailing platform activity.
- Driver supply is simulated independently of demand.
- Only 15 zone clusters are available for clustered inference.
- Synthetic driver assignment does not model complete real-world driver scheduling and availability constraints.
- The findings demonstrate analytical methodology rather than establishing real-world causal effects.

## Running the Project

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure PostgreSQL credentials in a local `.env` file.

Create the database and tables using:

```bash
psql -h localhost -p 5433 -U marketplace_user \
-d marketplace_analytics -f database/schema.sql
```

Run the data-generation scripts:

```bash
python scripts/generate_data.py
python scripts/generate_observations.py
python scripts/generate_rides.py
```

Run the statistical analyses:

```bash
python scripts/clustered_pricing_analysis.py
python scripts/randomization_inference.py
```

Launch the dashboard:

```bash
streamlit run dashboard/app.py
```

## Conclusion

This project demonstrates an end-to-end analytics workflow combining relational data modelling, SQL-based business analysis, statistical experimentation, regression modelling, randomization inference, and interactive dashboard development.
