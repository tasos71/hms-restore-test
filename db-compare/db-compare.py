import pytest
import os
from sqlalchemy import create_engine, text, inspect


# Read connection details from environment variables
SRC_USER = os.getenv('SRC_DB_USER', 'hive')
SRC_PASSWORD = os.getenv('SRC_DB_PASSWORD', 'abc123!')
SRC_HOST = os.getenv('SRC_DB_HOST', 'hive-metastore-db')
SRC_PORT = os.getenv('SRC_DB_PORT', '5432')
SRC_DBNAME = os.getenv('SRC_DB_NAME', 'metastore_db')

TGT_USER = os.getenv('TGT_DB_USER', 'hive')
TGT_PASSWORD = os.getenv('TGT_DB_PASSWORD', 'abc123!')
TGT_HOST = os.getenv('TGT_DB_HOST', 'hive-metastore-db')
TGT_PORT = os.getenv('TGT_DB_PORT', '5432')
TGT_DBNAME = os.getenv('TGT_DB_NAME', 'metastore_db')

# Construct connection URLs
src_url = f'postgresql://{SRC_USER}:{SRC_PASSWORD}@{SRC_HOST}:{SRC_PORT}/{SRC_DBNAME}'
tgt_url = f'postgresql://{TGT_USER}:{TGT_PASSWORD}@{TGT_HOST}:{TGT_PORT}/{TGT_DBNAME}'
#tgt_url = f'duckdb:///md:my_db'

# Setup connections
src_engine = create_engine(src_url)
tgt_engine = create_engine(tgt_url)

def get_table_names():
    with src_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_type = 'BASE TABLE'
        """))
        return [row[0] for row in result]

def get_pk_columns(table):
    with src_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT a.attname AS column_name
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = 'public."{table}}"'::regclass
            AND i.indisprimary;
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

@pytest.mark.parametrize("table", tables)
def test_row_counts(table):
    with src_engine.connect() as conn:
        src_count = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
    
    with tgt_engine.connect() as conn:
        tgt_count = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
    
    assert src_count == tgt_count, f"Mismatch in table '{table}': {src_count} != {tgt_count}"

@pytest.mark.parametrize("table", tables)
def test_value_compare(table):
    if (table == 'COMPACTION_METRICS_CACHE' or table == 'WRITE_SET' or table == 'TXN_TO_WRITE_ID' or table == 'NEXT_WRITE_ID' 
        or table == 'MIN_HISTORY_WRITE_ID' or table == 'TXN_COMPONENTS' or table == 'COMPLETED_TXN_COMPONENTS' or table == 'TXN_LOCK_TBL'
        or table == 'NEXT_LOCK_ID' or table == 'NEXT_COMPACTION_QUEUE_ID' ):
        assert True
    else:
        with src_engine.connect() as conn:
            src_fingerprint: str = generate_fingerprint(src_engine, table, "public")

        with tgt_engine.connect() as conn:
            tgt_fingerprint: str = generate_fingerprint(tgt_engine, table, "public")

            assert src_fingerprint == tgt_fingerprint, f"Mismatch in table '{table}': {src_fingerprint} != {tgt_fingerprint}"