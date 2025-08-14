import pytest
import hashlib
import os
import io
from sqlalchemy import create_engine, text, inspect
import pandas as pd
import boto3


# Read connection details from environment variables
HMS_DB_USER = os.getenv('HMS_DB_USER', 'hive')
HMS_DB_PASSWORD = os.getenv('HMS_DB_PASSWORD', 'abc123!')
HMS_DB_HOST = os.getenv('HMS_DB_HOST', 'hive-metastore-db')
HMS_DB_PORT = os.getenv('HMS_DB_PORT', '5432')
HMS_DB_DBNAME = os.getenv('HMS_DB_NAME', 'metastore_db')

# Construct connection URLs
src_url = f'postgresql://{HMS_DB_USER}:{HMS_DB_PASSWORD}@{HMS_DB_HOST}:{HMS_DB_PORT}/{HMS_DB_DBNAME}'

# Setup connections
src_engine = create_engine(src_url)

# Create a session and S3 client
s3 = boto3.client('s3')

# Connect to MinIO or AWS S3
endpoint_url = os.getenv('S3_ENDPOINT_URL', 'http://localhost:9000')

baseline_bucket = os.getenv('S3_BASELINE_BUCKET', 'admin-bucket')
baseline_object_key = os.getenv('S3_BASELINE_OBJECT_NAME', 'baseline_s3.csv')


# Create S3 client configuration
s3_config = {"service_name": "s3"}
if endpoint_url:
    s3_config["endpoint_url"] = endpoint_url

s3 = boto3.client(**s3_config)

# Read the object
response = s3.get_object(Bucket=baseline_bucket, Key=baseline_object_key)

def get_s3_partitions_baseline():
    # `response['Body'].read()` returns bytes, decode to string
    csv_string = response['Body'].read().decode('utf-8')

    # Debug: print the content
    print(f"CSV content length: {len(csv_string)}")
    print(f"First 100 chars: {csv_string[:100]}")

    # Add error handling
    if not csv_string.strip():
        raise ValueError("CSV file is empty")

    # Wrap the string in a StringIO buffer
    csv_buffer = io.StringIO(csv_string)

    db_baseline = pd.read_csv(csv_buffer)
    return db_baseline

db_baseline = get_s3_partitions_baseline()

def get_latest_timestamp(db_baseline):
    
    latest_timestamp = db_baseline['timestamp'].max()

    return latest_timestamp

def get_hms_partitions_count_and_partnames(s3_location: str, end_timestamp: int):
    with src_engine.connect() as conn:
        # TODO: Make end_timestamp optional and configure number of seconds to add
        result = conn.execute(text(f"""
            SELECT t."TBL_NAME", t."TBL_TYPE", p."partition_count", p."part_names"
            FROM (
                SELECT p."TBL_ID",
                    COUNT(*) AS partition_count,
                    string_agg(p."PART_NAME", ',' ORDER BY p."PART_NAME")   part_names
                FROM public."PARTITIONS" p
                WHERE p."CREATE_TIME" <= {end_timestamp} + 1                 
                GROUP BY p."TBL_ID"
            ) p
            JOIN (
                SELECT t."TBL_ID",
                    t."CREATE_TIME",
                    t."TBL_NAME",
                    t."TBL_TYPE"
                FROM public."TBLS" t
                JOIN public."DBS" d ON t."DB_ID" = d."DB_ID"
                JOIN public."SDS" s ON t."SD_ID" = s."SD_ID"
                WHERE s."LOCATION" = '{s3_location}'
            ) t
            ON t."TBL_ID" = p."TBL_ID";
        """))
        row = result.mappings().one_or_none()  # strict: must return exactly one row
        return row

def quote_ident(name: str, dialect):
    return dialect.identifier_preparer.quote(name)


# Dynamically get the s3 locations from the baseline file
s3_locations = db_baseline["s3_location"].tolist()
max_timestamp = get_latest_timestamp(db_baseline)
partition_counts = db_baseline.set_index("s3_location")["partition_count"].to_dict()
partition_fingerprint = db_baseline.set_index("s3_location")["fingerprint"].to_dict()

@pytest.mark.parametrize("s3_location", s3_locations)
def test_partition_counts(s3_location):
    partition = get_hms_partitions_count_and_partnames(s3_location, max_timestamp)
    assert partition is not None, f"Expected a row for {s3_location} from HMS select query, but got None"
    assert partition_counts[s3_location] == partition["partition_count"], f"Partition count mismatch for {s3_location} in Hive Metastore: expected {partition_counts[s3_location]} (S3), but got {partition["partition_count"]} (HMS)"

@pytest.mark.parametrize("s3_location", s3_locations)
def test_partition_fingerprints(s3_location):
    partition = get_hms_partitions_count_and_partnames(s3_location, max_timestamp)
    assert partition is not None, f"Expected a row for {s3_location} from HMS select query, but got None"

    # part_names is a comma-separated string of partition names
    fingerprint = hashlib.sha256(partition["part_names"].encode('utf-8')).hexdigest()

    assert partition_fingerprint[s3_location] == fingerprint, f"Partition fingerprint mismatch for {s3_location} in Hive Metastore: expected {partition_fingerprint[s3_location]} (S3), but got {fingerprint} (HMS)"