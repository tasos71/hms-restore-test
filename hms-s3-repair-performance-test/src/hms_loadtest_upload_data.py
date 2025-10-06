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

def loadtest_upload_flights(end_year=2010, num_tables=1000, num_objects=5, do_repair=False, use_large=False):
    # Upload flights data
    for year in range(2008, end_year):
        # For each year, iterate through months
        for month in range(1, 13):
            for nof_objects in range(0, num_objects):
                for table_num in range(0, num_tables):
                # Upload objects per month
                    output = hms_loadtest_base.upload_flights_with_timestamp(year, month, table_num, nof_objects, use_large=use_large, duplicateIt=False)
                    assert 0 == int(output.exit_code), f"Failed to upload flights data for period {1} to table flights_{table_num}_t: {output.output.decode('utf-8')}"
                    if do_repair:
                        hms_loadtest_base.do_trino_repair(table_num)

def loadtest_upload_airports(num_tables=1000):
    # Upload airports data
    for table_num in range(0, num_tables):
        # Upload objects per month
        output = hms_loadtest_base.upload_airports(table_num)
        assert 0 == int(output.exit_code), f"Failed to upload airports to table airports_{table_num}_t: {output.output.decode('utf-8')}"

if __name__ == "__main__":
    # Default values
    end_year = 2010
    num_tables = 1000
    num_objects = 5
    
    # Parse command-line arguments
    if len(sys.argv) > 1:
        try:
            table_type = sys.argv[1]
            num_tables = int(sys.argv[2])
            if len(sys.argv) > 3:
                num_objects = int(sys.argv[3])
            if len(sys.argv) > 4:
                end_year = int(sys.argv[4])
            do_repair = False
            if len(sys.argv) > 5:
                do_repair_arg = sys.argv[5].lower()
                if do_repair_arg in ("1", "true", "yes"):
                    do_repair = True
            use_large = False
            if len(sys.argv) > 6:
                use_large_arg = sys.argv[6].lower()
                if use_large_arg in ("1", "true", "yes"):
                    use_large = True
        except ValueError:
            print("Error: Please provide valid integers for the arguments.")
            print("Usage: python hms_loadtest_upload_data.py [table_type] [num_tables] [num_objects] [end_year] [do_repair] [use_large]")
            print("Example: python hms_loadtest_upload_data.py flights 500 3 2012 True False")
            print("Example2: python hms_loadtest_upload_data.py airports 1")
            sys.exit(1)
    
    print("Starting upload test with:")
    print(f"  Table type: {table_type}")
    print(f"  Number of tables: {num_tables}")
    print(f"  Number of objects per table/month: {num_objects}")
    print(f"  Year range: 2008 to {end_year-1}")
    
    print(f"  Do repair: {do_repair}")
    print(f"  Use large files: {use_large}")

    if table_type == 'flights':
        loadtest_upload_flights(end_year, num_tables, num_objects, do_repair=do_repair, use_large=use_large)
    elif table_type == 'airports':
        loadtest_upload_airports(num_tables=num_tables)