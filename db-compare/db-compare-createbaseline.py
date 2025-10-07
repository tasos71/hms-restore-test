import pytest
import os
from sqlalchemy import create_engine, select, text, Column, Integer, String, DateTime, inspect

import json


# Read connection details from environment variables
SRC_USER = os.getenv('SRC_DB_USER', 'hive')
SRC_PASSWORD = os.getenv('SRC_DB_PASSWORD', 'abc123!')
SRC_HOST = os.getenv('SRC_DB_HOST', 'localhost')
SRC_PORT = os.getenv('SRC_DB_PORT', '5442')
SRC_DBNAME = os.getenv('SRC_DB_NAME', 'metastore_db')

# Construct connection URLs
src_url = f'postgresql://{SRC_USER}:{SRC_PASSWORD}@{SRC_HOST}:{SRC_PORT}/{SRC_DBNAME}'


# Setup connections
src_engine = create_engine(src_url)

def get_table_names():
    with src_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_type = 'BASE TABLE'
        """))
        return [row[0] for row in result]

def quote_ident(name: str, dialect):
    return dialect.identifier_preparer.quote(name)

def generate_baseline_for_table(engine, table: str, schema: str = "public") -> str:
    with engine.connect() as conn:
        # Step 1: Get primary key columns
        inspector = inspect(conn)
        pk_columns = inspector.get_pk_constraint(table, schema=schema)['constrained_columns']

        if not pk_columns:
            print(f"No primary key found for table {schema}.{table}")
        else:
            # Step 2: Quote identifiers for safety
            full_table = f"{schema}.{quote_ident(table,dialect=conn.dialect)}"
            order_by_clause = ", ".join("t." + quote_ident(col,dialect=conn.dialect) for col in pk_columns)

            print (f"Generating fingerprint for table {full_table} using PK columns: {pk_columns}")

            create_time_table_join = ""
            create_time_col = ""
            create_time_col_alias = ""
            if "PART_ID" in pk_columns:
                create_time_table_join = "LEFT JOIN public.\"PARTITIONS\" ct ON ct.\"PART_ID\" = t.\"PART_ID\""
                create_time_col = ', ct."CREATE_TIME" AS create_time'
                create_time_col_alias = ', MAX(create_time) AS max_create_time'
            if "TBL_ID" in pk_columns:
                create_time_table_join = "LEFT JOIN public.\"TBLS\" ct ON ct.\"TBL_ID\" = t.\"TBL_ID\""
                create_time_col = ', ct."CREATE_TIME" AS create_time'
                create_time_col_alias = ', MAX(create_time) AS max_create_time'
            if "DB_ID" in pk_columns:
                create_time_table_join = "LEFT JOIN public.\"DBS\" ct ON ct.\"DB_ID\" = t.\"DB_ID\""
                create_time_col = ', ct."CREATE_TIME" AS create_time'
                create_time_col_alias = ', MAX(create_time) AS max_create_time'

            # Step 3: Prepare and execute SQL
            query = text(f"""
                SELECT COUNT(*) AS row_count
                , md5(string_agg(md5(row_text), '')) AS fingerprint
                {create_time_col_alias}
                FROM (
                    SELECT row(t.*)::text AS row_text
                    {create_time_col}
                    FROM {full_table} t
                    {create_time_table_join}
                    ORDER BY {order_by_clause}
                ) AS subquery  
            """)

            print (f"Executing query: {query}")

            result = conn.execute(query)
            row = result.fetchone()
        return row

# Dynamically get table names from the source DB
tables = get_table_names()

def create_baseline():
    tables = get_table_names()

    S3_BASELINE_OBJECT_NAME = "hms_baseline.csv"
    with open(S3_BASELINE_OBJECT_NAME, "w") as f:
        # Print CSV header
        print("table_name,count,fingerprint,timestamp", file=f)

        for table in tables:
            if (table == 'COMPACTION_METRICS_CACHE' or table == 'WRITE_SET' or table == 'TXN_TO_WRITE_ID' or table == 'NEXT_WRITE_ID' 
                or table == 'MIN_HISTORY_WRITE_ID' or table == 'TXN_COMPONENTS' or table == 'COMPLETED_TXN_COMPONENTS' or table == 'TXN_LOCK_TBL'
                or table == 'NEXT_LOCK_ID' or table == 'NEXT_COMPACTION_QUEUE_ID' ):
                continue
            else:
                with src_engine.connect() as conn:
                    baseline = generate_baseline_for_table(src_engine, table, "public")

                if baseline is not None:
                    count = baseline[0]
                    if baseline[1] is not None:
                        fingerprint = baseline[1]
                    else:
                        fingerprint = ''
                    timestamp = baseline[2] if len(baseline) > 2 else 0
                    print(f"{table},{count},{fingerprint},{timestamp}", file=f)
                    

create_baseline()