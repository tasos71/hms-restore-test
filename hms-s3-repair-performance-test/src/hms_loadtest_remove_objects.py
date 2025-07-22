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

#docker.DockerClient(base_url='tcp://127.0.0.1:2375')
client = docker.from_env()

def loadtest_remove(num_tables=1000, max_objects=5, year=2009, month=12):
    # Remove flights data objects
    for table_num in range(0, num_tables):
        for nof in range(3, max_objects):
            output = hms_loadtest_base.remove_object(year, month, table_num, nof)
            assert 0 == int(output.exit_code), f"Failed to remove flights data for period {year}-{month} to table flights_{table_num}_t: {output.output.decode('utf-8')}"

if __name__ == "__main__":
    # Default values
    num_tables = 1000
    max_objects = 5
    year = 2009
    month = 12
    
    # Parse command-line arguments
    if len(sys.argv) > 1:
        try:
            num_tables = int(sys.argv[1])
            if len(sys.argv) > 2:
                max_objects = int(sys.argv[2])
            if len(sys.argv) > 3:
                year = int(sys.argv[3])
            if len(sys.argv) > 4:
                month = int(sys.argv[4])
                
            # Validate month range
            if not (1 <= month <= 12):
                print("Error: Month must be between 1 and 12.")
                sys.exit(1)
                
        except ValueError:
            print("Error: Please provide valid integers for the arguments.")
            print("Usage: python hms_loadtest_remove_objects.py [num_tables] [max_objects] [year] [month]")
            print("Example: python hms_loadtest_remove_objects.py 500 3 2010 6")
            sys.exit(1)
    
    print("Starting object removal test with:")
    print(f"  Number of tables: {num_tables}")
    print(f"  Max objects per table: {max_objects} (removing objects 3 to {max_objects-1})")
    print(f"  Target partition: {year}-{month:02d}")
    
    loadtest_remove(num_tables, max_objects, year, month)

