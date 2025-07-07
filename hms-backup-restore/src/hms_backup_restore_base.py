import pytest
import os
import docker
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
            CREATE SCHEMA IF NOT EXISTS minio.flight_db
        """))

def create_airport_table():
    with trino_engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE minio.flight_db.airport_t (
                id               VARCHAR,
                ident            VARCHAR,
                type             VARCHAR,
                name             VARCHAR,
                latitude_deg     VARCHAR,
                longitude_deg    VARCHAR,
                elevation_ft     VARCHAR,
                continent        VARCHAR,
                iso_country      VARCHAR,
                iso_region       VARCHAR,
                municipality     VARCHAR,
                scheduled_service VARCHAR,
                gps_code         VARCHAR,
                iata_code        VARCHAR,
                local_code       VARCHAR,
                home_link        VARCHAR,
                wikipedia_link   VARCHAR,
                keywords         VARCHAR
            )
            WITH (
                external_location = 's3a://flight-bucket/raw/airports/',
                format = 'CSV',
                skip_header_line_count = 1
            )
        """))

def create_flights_table():
    with trino_engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE minio.flight_db.flights_t (
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
                external_location = 's3a://flight-bucket/refined/flights/',
                format = 'PARQUET',
                partitioned_by = ARRAY['year', 'month']
            )
        """))


def create_flights_per_carrier_table():
    with trino_engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE minio.flight_db.flights_per_carrier_t (
                uniquecarrier VARCHAR,
                flight_count INTEGER
            )
            WITH (
                external_location = 's3a://flight-bucket/refined/flights-per-carrier',
                format = 'PARQUET'
            )
        """))

    with trino_engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO minio.flight_db.flights_per_carrier_t 
            SELECT uniquecarrier, COUNT(*) AS flight_count 
            FROM minio.flight_db.flights_t GROUP BY uniquecarrier
        """))


def get_count(table):
    with trino_engine.connect() as conn:
        count = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
    return count

def upload_airport(period):
    # Run a temporary container (e.g., alpine echo)
    output = client.containers.get('minio-mc').exec_run(
        cmd=f"mc rm minio-1/flight-bucket/raw/airports/airports-{period-1}.csv",
    )

    output = client.containers.get('minio-mc').exec_run(
        cmd=f"mc cp /data-transfer/airport-data/airports-{period}.csv minio-1/flight-bucket/raw/airports/airports-{period}.csv",
    )

    return output

def upload_flights(period):
    # Run a temporary container (e.g., alpine echo)
    output = client.containers.get('minio-mc').exec_run(
        cmd=f"mc cp --recursive /data-transfer/flight-data/flights-medium-parquet-partitioned/flights/year=2008/month={period} minio-1/flight-bucket/refined/flights/year=2008/",
    )

    return output

def backup_minio(period):
    # Run a temporary container (e.g., alpine echo)
    output = client.containers.get('minio-mc').exec_run(
        cmd=f"cp -R container-volume/minio/ backup/{period}",
    )

    return output

def backup_hms(savepoint):
    # Run a temporary container (e.g., alpine echo)
    output = client.containers.get('hive-metastore-db').exec_run(
        cmd=f"pg_dump -U hive -d metastore_db -F c -f /hms-{savepoint}.dump",
    )

    return output

def do_mck_repair():
    # Run a temporary container (e.g., alpine echo)
    output = client.containers.get('hive-metastore').exec_run(
        cmd=f"hive -e 'MSCK REPAIR TABLE flight_db.flights_t;",
    )

    return output

def do_mck_repair():
    # Run a temporary container (e.g., alpine echo)
    output = client.containers.get('hive-metastore').exec_run(
        cmd=f"hive -e 'MSCK REPAIR TABLE flight_db.flights_t;",
    )

    return output

def do_trino_repair():
    with trino_engine.connect() as conn:
        conn.execute(text(f"call minio.system.sync_partition_metadata('flight_db', 'flights_t', 'FULL')"))

def assert_count(table, expected_count):
    airport_count = get_count(table)
    
    assert expected_count == airport_count, f"Mismatch in table '{table}': {expected_count} != {airport_count}"

def assert_notifications(expected_event_types):
    with trino_engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT nl_id, event_type
                FROM hive_metastore_db.public.notification_log
                ORDER BY nl_id
            """),
        )
        actual_event_types = [row.event_type for row in result]

    assert actual_event_types == expected_event_types, (
        f"Mismatch in event_types for table 'notification_log':\n"
        f"Expected: {expected_event_types}\n"
        f"Found: {actual_event_types}"
    )

