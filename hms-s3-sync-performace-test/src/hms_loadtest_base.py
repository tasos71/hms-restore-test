import pytest
import os
import docker
import shutil
from sqlalchemy import create_engine,text


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

def create_schema():
    with trino_engine.connect() as conn:
        conn.execute(text("""
            CREATE SCHEMA minio.flight_db
        """))

def create_flights_table(num):
    with trino_engine.connect() as conn:
        conn.execute(text(f"""
            DROP TABLE IF EXISTS minio.flight_db.flights_{num}_t
        """))        
        conn.execute(text(f"""
            CREATE TABLE minio.flight_db.flights_{num}_t (
                dayOfMonth         INTEGER,
                dayOfWeek          INTEGER,
                depTime            INTEGER,
                crsDepTime         INTEGER,
                arrTime            INTEGER,
                crsArrTime         INTEGER,
                uniqueCarrier      VARCHAR,
                flightNum          VARCHAR,
                tailNum            VARCHAR,
                actualElapsedTime  INTEGER,
                crsElapsedTime     INTEGER,
                airTime            INTEGER,
                arrDelay           INTEGER,
                depDelay           INTEGER,
                origin             VARCHAR,
                destination        VARCHAR,
                distance           INTEGER,
                year               INTEGER,
                month              INTEGER
            )
            WITH (
                external_location = 's3a://flight-bucket/refined/flights_{num}_t/',
                format = 'PARQUET',
                partitioned_by = ARRAY['year', 'month']
            )
        """))

def get_count(table):
    with trino_engine.connect() as conn:
        count = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
    return count

def upload_flights(year, month, table_num, nof):
    # Run a temporary container (e.g., alpine echo)
    output = client.containers.get('minio-mc').exec_run(
        cmd=f"mc cp  /data-transfer/flight-data/flights-tiny-parquet/part-00009-3ca3adb9-4e4b-4d8d-a60f-89a77615c374.c000.snappy.parquet minio-1/flight-bucket/refined/flights_{table_num}_t/year={year}/month={month}/{nof}.snappy.parquet",
    )

    return output

def remove_object(year, month, table_num, nof):
    # Run a temporary container (e.g., alpine echo)
    output = client.containers.get('minio-mc').exec_run(
        cmd=f"mc rm minio-1/flight-bucket/refined/flights_{table_num}_t/year={year}/month={month}/{nof}.snappy.parquet",
    )

    return output

def remove_partition(year, month, table_num):
    # Run a temporary container (e.g., alpine echo)
    output = client.containers.get('minio-mc').exec_run(
        cmd=f"mc rm -r --force minio-1/flight-bucket/refined/flights_{table_num}_t/year={year}/month={month}",
    )

    return output

def backup_minio(period):
    # Run a temporary container (e.g., alpine echo)

    source_folder = "../platys-hms/container-volume/minio/"
    destination_folder = f"../platys-hms/backup/{period}"

    shutil.copytree(source_folder, destination_folder)

def do_trino_repair(num):
    with trino_engine.connect() as conn:
        conn.execute(text(f"call minio.system.sync_partition_metadata('flight_db', 'flights_{num}_t', 'FULL')"))

def assert_count(table, expected_count):
    airport_count = get_count(table)
    
    assert expected_count == airport_count, f"Mismatch in table '{table}': {expected_count} != {airport_count}"


