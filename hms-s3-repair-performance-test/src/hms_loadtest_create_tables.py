import os
import sys
import docker
from sqlalchemy import create_engine,text
import timeit

from src import hms_loadtest_base

# Read connection details from environment variables
HMS_USER = os.getenv('HMS_DB_USER', 'hive')
HMS_PASSWORD = os.getenv('HMS_DB_PASSWORD', 'abc123!')
HMS_HOST = os.getenv('HMS_DB_HOST', 'localhost')
HMS_PORT = os.getenv('HMS_DB_PORT', '5442')
HMS_DBNAME = os.getenv('HMS_DB_NAME', 'metastore_db')

TRINO_USER = os.getenv('TRINO_DB_USER', 'trino')
TRINO_PASSWORD = os.getenv('TRINO_DB_PASSWORD', '')
TRINO_HOST = os.getenv('TRINO_DB_HOST', 'localhost')
TRINO_PORT = os.getenv('TRINO_DB_PORT', '28082')
TRINO_SCHEMA = os.getenv('TRINO_SCHEMA', 'flight_db')

# Construct connection URLs
hms_url = f'postgresql://{HMS_USER}:{HMS_PASSWORD}@{HMS_HOST}:{HMS_PORT}/{HMS_DBNAME}'
trino_url = f'trino://{TRINO_USER}:{TRINO_PASSWORD}@{TRINO_HOST}:{TRINO_PORT}/minio/{TRINO_SCHEMA}'

# Setup connections
hms_engine = create_engine(hms_url)
trino_engine = create_engine(trino_url)

client = docker.from_env()

def loadtest_create_tables(num_tables=1000):
    # Create schema and tables
    try:
        hms_loadtest_base.create_schema()
    except Exception as e:
        print(f"Error creating schema: {e}")

    for table_num in range(0, num_tables):
        hms_loadtest_base.create_flights_table(table_num)

if __name__ == "__main__":
    # Default number of tables
    num_tables = 1000
    
    # Check if number of tables is provided as command-line argument
    if len(sys.argv) > 1:
        try:
            num_tables = int(sys.argv[1])
            print(f"Creating {num_tables} tables...")
        except ValueError:
            print("Error: Please provide a valid integer for the number of tables.")
            print("Usage: python hms_loadtest_create_tables.py [number_of_tables]")
            sys.exit(1)
    else:
        print(f"Creating {num_tables} tables (default)...")
    
    loadtest_create_tables(num_tables)

