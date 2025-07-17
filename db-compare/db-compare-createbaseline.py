import pytest
import os
from sqlalchemy import create_engine, text, inspect
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

def generate_fingerprint(engine, table: str, schema: str = "public") -> str:
    with engine.connect() as conn:
        # Step 1: Get primary key columns
        inspector = inspect(conn)
        pk_columns = inspector.get_pk_constraint(table, schema=schema)['constrained_columns']

        if not pk_columns:
            print(f"No primary key found for table {schema}.{table}")
        else:
            # Step 2: Quote identifiers for safety
            full_table = f"{schema}.{quote_ident(table,dialect=conn.dialect)}"
            order_by_clause = ", ".join(quote_ident(col,dialect=conn.dialect) for col in pk_columns)

            # Step 3: Prepare and execute SQL
            query = text(f"""
                SELECT md5(string_agg(md5(row_text), '')) AS fingerprint
                FROM (
                    SELECT row(t.*)::text AS row_text
                    FROM {full_table} t
                    ORDER BY {order_by_clause}
                ) AS subquery  
            """)

            result = conn.execute(query).scalar()
        return result

# Dynamically get table names from the source DB
tables = get_table_names()

def save_table_counts():
    src_count = {}
    with src_engine.connect() as conn:
        for table in tables:
            src_count[table] = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
    
    with open('counts.json', 'w') as f:
        json.dump(src_count, f, indent=4)

def save_table_fingerprints():
    src_fingerprint = {}
    tables = get_table_names()

    for table in tables:
        if (table == 'COMPACTION_METRICS_CACHE' or table == 'WRITE_SET' or table == 'TXN_TO_WRITE_ID' or table == 'NEXT_WRITE_ID' 
            or table == 'MIN_HISTORY_WRITE_ID' or table == 'TXN_COMPONENTS' or table == 'COMPLETED_TXN_COMPONENTS' or table == 'TXN_LOCK_TBL'
            or table == 'NEXT_LOCK_ID' or table == 'NEXT_COMPACTION_QUEUE_ID' ):
            continue
        else:
            with src_engine.connect() as conn:
                src_fingerprint[table] = generate_fingerprint(src_engine, table, "public")

    with open('fingerprints.json', 'w') as f:
        json.dump(src_fingerprint, f, indent=4)

save_table_fingerprints()
save_table_counts()