import pytest
import os
from sqlalchemy import create_engine, text, inspect
import pandas as pd


# Read connection details from environment variables
SRC_USER = os.getenv('SRC_DB_USER', 'hive')
SRC_PASSWORD = os.getenv('SRC_DB_PASSWORD', 'abc123!')
SRC_HOST = os.getenv('SRC_DB_HOST', 'hive-metastore-db')
SRC_PORT = os.getenv('SRC_DB_PORT', '5432')
SRC_DBNAME = os.getenv('SRC_DB_NAME', 'metastore_db')

# Construct connection URLs
src_url = f'postgresql://{SRC_USER}:{SRC_PASSWORD}@{SRC_HOST}:{SRC_PORT}/{SRC_DBNAME}'

# Setup connections
src_engine = create_engine(src_url)

def get_s3_partitions_baseline():
    db_baseline = pd.read_csv("baseline_metrics.csv")
    return db_baseline

def get_latest_timestamp(db_baseline):
    db_baseline = get_s3_partitions_baseline()
    latest_timestamp = db_baseline['timestamp'].max()

    return latest_timestamp

def get_count_by_s3_location(db_baseline, s3_location):
    db_baseline = get_s3_partitions_baseline()['s3_location'] == s3_location
    latest_timestamp = db_baseline['timestamp'].max()

    return latest_timestamp


def get_hms_partitions_count(s3_location: str, epoc_timestamp: int):
    with src_engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT t."TBL_NAME", t."TBL_TYPE", p."partition_count"
            FROM (
                SELECT p."TBL_ID",
                    COUNT(*) AS partition_count
                FROM public."PARTITIONS" p
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


# Dynamically get table names from the source DB
s3_locations = get_s3_partitions_baseline()["s3_location"].tolist()
max_timestamp = get_latest_timestamp(get_s3_partitions_baseline())
partition_counts = get_s3_partitions_baseline().set_index("s3_location")["partition_count"].to_dict()

@pytest.mark.parametrize("s3_location", s3_locations)
def test_partition_counts(s3_location):
    partition = get_hms_partitions_count(s3_location, max_timestamp)
    assert partition is not None, f"Expected a row for {s3_location} from HMS select query, but got None"
    assert partition_counts[s3_location] == partition["partition_count"], f"Partition count mismatch for {s3_location}: expected {partition_counts[s3_location]}, got {partition["partition_count"]}"
