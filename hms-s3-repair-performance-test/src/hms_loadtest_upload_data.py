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

def loadtest_upload(end_year=2010, num_tables=1000, num_objects=5, use_large=False):
    # Upload flights data
    for year in range(2008, end_year):
        # For each year, iterate through months
        for month in range(1, 13):
            for nof_objects in range(0, num_objects):
                for table_num in range(0, num_tables):
                # Upload objects per month
                    output = hms_loadtest_base.upload_flights_with_timestamp(year, month, table_num, nof_objects, use_large=use_large, duplicateIt=False)
                    assert 0 == int(output.exit_code), f"Failed to upload flights data for period {1} to table flights_{table_num}_t: {output.output.decode('utf-8')}"
                    hms_loadtest_base.do_trino_repair(table_num)

if __name__ == "__main__":
    # Default values
    end_year = 2010
    num_tables = 1000
    num_objects = 5
    
    # Parse command-line arguments
    if len(sys.argv) > 1:
        try:
            end_year = int(sys.argv[1])
            if len(sys.argv) > 2:
                num_tables = int(sys.argv[2])
            if len(sys.argv) > 3:
                num_objects = int(sys.argv[3])
            use_large = False
            if len(sys.argv) > 4:
                use_large_arg = sys.argv[4].lower()
                if use_large_arg in ("1", "true", "yes"):
                    use_large = True
        except ValueError:
            print("Error: Please provide valid integers for the arguments.")
            print("Usage: python hms_loadtest_upload_data.py [end_year] [num_tables] [num_objects]")
            print("Example: python hms_loadtest_upload_data.py 2012 500 3")
            sys.exit(1)
    
    print("Starting upload test with:")
    print(f"  Year range: 2008 to {end_year-1}")
    print(f"  Number of tables: {num_tables}")
    print(f"  Number of objects per table/month: {num_objects}")
    

    print(f"  Use large files: {use_large}")

    loadtest_upload(end_year, num_tables, num_objects, use_large=use_large)