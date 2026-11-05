import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load credentials from .env
load_dotenv()

# Read database configuration
DB_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)

# Create database engine
engine = create_engine(DB_URL)

# Test connection
with engine.connect() as connection:
    result = connection.execute(text("SELECT version();"))
    print("Connected successfully!")
    print(result.scalar())