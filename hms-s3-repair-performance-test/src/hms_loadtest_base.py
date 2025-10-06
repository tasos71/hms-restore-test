import pytest
import os
import docker
import shutil
import boto3
from sqlalchemy import create_engine,text
import pandas as pd


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

DATAPLATFORM_HOME = os.getenv('DATAPLATFORM_HOME', '/home/gschmutz/dev/dataplatform')

# Setup connections
hms_engine = create_engine(hms_url)
trino_engine = create_engine(trino_url)

#docker.DockerClient(base_url='tcp://127.0.0.1:2375')
client = docker.from_env()

endpoint_url = os.getenv('S3_ENDPOINT_URL', 'http://localhost:9000')
bucket = os.getenv('S3_BUCKET', 'flight-bucket')
prefix = os.getenv('S3_PREFIX', 'refined')  # optionally, specify a prefix
aws_access_key = os.getenv('AWS_ACCESS_KEY', None)
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY', None)

# Add S3/MinIO client configuration
def get_s3_client():
    """Get S3 client configured for MinIO or AWS S3"""
    
    # Build client arguments conditionally
    client_args = {}
    if endpoint_url:
        client_args['endpoint_url'] = endpoint_url
    if aws_access_key and aws_secret_access_key:
        client_args["aws_access_key_id"] = aws_access_key
        client_args["aws_secret_access_key"] = aws_secret_access_key

    return boto3.client("s3", **client_args)

s3_client = get_s3_client()

def create_bucket(bucket_name):
    # Create S3/MinIO bucket if it doesn't exist
    try:
        print(f"Creating bucket '{bucket_name}'...")
        s3_client.create_bucket(Bucket=bucket_name)
    except Exception as e:
        print(f"Error checking/creating bucket: {e}")

def enable_bucket_versioning(bucket_name):
    # Enable versioning on the bucket
    try:
        s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print(f"Versioning enabled on bucket '{bucket_name}'.")
    except Exception as e:
        print(f"Error enabling versioning: {e}")

def create_schema():
    with trino_engine.connect() as conn:
        conn.execute(text("""
            CREATE SCHEMA minio.flight_db
        """))

def create_airports_table(num):
    with trino_engine.connect() as conn:
        conn.execute(text(f"""
            DROP TABLE IF EXISTS minio.flight_db.airports_{num}_t
        """))        
        conn.execute(text(f"""
            CREATE TABLE minio.flight_db.airports_{num}_t (
                id               INTEGER,
                ident            VARCHAR,
                type             VARCHAR,
                name             VARCHAR,
                latitude_deg     DOUBLE,
                longitude_deg    DOUBLE,
                elevation_ft     INTEGER,
                continent        VARCHAR,
                iso_country      VARCHAR,
                iso_region       VARCHAR,
                municipality     VARCHAR,
                scheduled_service VARCHAR,
                gps_code        VARCHAR,
                iata_code       VARCHAR,
                local_code      VARCHAR,
                home_link       VARCHAR,
                wikipedia_link  VARCHAR,    
                keywords        VARCHAR                     
            )
            WITH (
                external_location = 's3a://flight-bucket/refined/airports_{num}_t/',
                format = 'JSON'
            )
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
                eventTimestamp     TIMESTAMP,
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

def upload_airports(table_num):
    # Run a temporary container (e.g., alpine echo)
    output = client.containers.get('minio-mc').exec_run(
        cmd=f"mc cp /data-transfer/airport-data/airports.json minio-1/flight-bucket/refined/airports_{table_num}_t/",
    )

    return output

def upload_flights(year, month, table_num, nof):
    # Run a temporary container (e.g., alpine echo)
    output = client.containers.get('minio-mc').exec_run(
        cmd=f"mc cp  /data-transfer/flight-data/flights-parquet/flight-small.snappy.parquet minio-1/flight-bucket/refined/flights_{table_num}_t/year={year}/month={month}/{nof}.snappy.parquet",
    )

    return output

def upload_flights_with_timestamp_nolongerused(year, month, table_num, nof, use_large=False):
    if use_large:
        parquet_file = f'{DATAPLATFORM_HOME}/data-transfer/flight-data/flights-parquet/flight-large.snappy.parquet'  # large
    else:
        parquet_file = f'{DATAPLATFORM_HOME}/data-transfer/flight-data/flights-parquet/flight-small.snappy.parquet'  # small

    df = pd.read_parquet(parquet_file)

    df['year'] = year
    df['month'] = month
    index_of_year = df.columns.get_loc('year')
    df.insert(loc=index_of_year, column='eventTimestamp', value=pd.Timestamp.now())

    df.to_parquet(f"{DATAPLATFORM_HOME}/data-transfer/flight-data/flights-parquet/flight.snappy.parquet", index=False)

    # Run a temporary container (e.g., alpine echo)
    output = client.containers.get('minio-mc').exec_run(
        cmd=f"mc cp  /data-transfer/flight-data/flights-parquet/flight.snappy.parquet minio-1/flight-bucket/refined/flights_{table_num}_t/year={year}/month={month}/{nof}.snappy.parquet",
    )

    return output

def upload_flights_with_timestamp(year, month, table_num, nof, use_large=False, duplicateIt=False):
    if use_large:
        parquet_file = f'{DATAPLATFORM_HOME}/data-transfer/flight-data/flights-parquet/flight-large.snappy.parquet'  # large
    else:
        parquet_file = f'{DATAPLATFORM_HOME}/data-transfer/flight-data/flights-parquet/flight-small.snappy.parquet'  # small

    df = pd.read_parquet(parquet_file)

    df['year'] = year
    df['month'] = month
    index_of_year = df.columns.get_loc('year')
    df.insert(loc=index_of_year, column='eventTimestamp', value=pd.Timestamp.now())

    if duplicateIt:
        df_extended = df.copy()
        for copy in range(0, 9):
            df_extended = pd.concat([df_extended, df], ignore_index=True)

        df_extended.to_parquet(f"{DATAPLATFORM_HOME}/data-transfer/flight-data/flights-parquet/flight.snappy.parquet", index=False)
    else:
        df.to_parquet(f"{DATAPLATFORM_HOME}/data-transfer/flight-data/flights-parquet/flight.snappy.parquet", index=False)

    # Run a temporary container (e.g., alpine echo)
    output = client.containers.get('minio-mc').exec_run(
        cmd=f"mc cp  /data-transfer/flight-data/flights-parquet/flight.snappy.parquet minio-1/flight-bucket/refined/flights_{table_num}_t/year={year}/month={month}/{nof}.snappy.parquet",
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
        cmd=f"mc rm --recursive --force --versions minio-1/flight-bucket/refined/flights_{table_num}_t/year={year}/month={month}/",
    )

    return output

def remove_partition_boto3(bucket, prefix, year, month, table_num):
    """Remove partition using boto3 instead of mc command"""
    s3_client = get_s3_client()
    
    bucket = "flight-bucket"
    prefix = f"refined/flights_{table_num}_t/year={year}/month={month}/"
    
    try:
        # List all objects in the partition
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
        
        objects_to_delete = []
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    objects_to_delete.append({'Key': obj['Key']})
        
        # Delete objects in batches (max 1000 per batch)
        if objects_to_delete:
            # Split into batches of 1000 (AWS S3 limit)
            batch_size = 1000
            for i in range(0, len(objects_to_delete), batch_size):
                batch = objects_to_delete[i:i + batch_size]
                
                response = s3_client.delete_objects(
                    Bucket=bucket,
                    Delete={
                        'Objects': batch,
                        'Quiet': True
                    }
                )
    except Exception as e:
        print(f"Error removing partition {year}-{month} from table flights_{table_num}_t: {e}")
        return None        


def logically_delete_partition(location, partition_name):
    # Convert s3a:// location to minio path and construct full path
    # Convert "s3a://flight-bucket/refined/flights_999_t" to "minio-1/flight-bucket/refined/flights_999_t"
    minio_path = location.replace("s3a://", "minio-1/")
    full_path = f"{minio_path}/{partition_name}/"
    
    # Run a temporary container (e.g., alpine echo)
    output = client.containers.get('minio-mc').exec_run(
        cmd=f"mc rm --recursive --force {full_path}",
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


