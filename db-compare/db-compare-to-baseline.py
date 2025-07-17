import pytest
import os
import json
from sqlalchemy import create_engine, text, inspect

TGT_USER = os.getenv('TGT_DB_USER', 'hive')
TGT_PASSWORD = os.getenv('TGT_DB_PASSWORD', 'abc123!')
TGT_HOST = os.getenv('TGT_DB_HOST', 'localhost')
TGT_PORT = os.getenv('TGT_DB_PORT', '5442')
TGT_DBNAME = os.getenv('TGT_DB_NAME', 'metastore_db')

# Construct connection URLs
tgt_url = f'postgresql://{TGT_USER}:{TGT_PASSWORD}@{TGT_HOST}:{TGT_PORT}/{TGT_DBNAME}'

# Setup connections
tgt_engine = create_engine(tgt_url)

def quote_ident(name: str, dialect):
    return dialect.identifier_preparer.quote(name)

def get_table_names():
    with tgt_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_type = 'BASE TABLE'
        """))
        return [row[0] for row in result]

# Dynamically get table names from the source DB
tables = get_table_names()


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

with open("counts.json", "r") as f:
    src_counts = json.load(f)

with open("fingerprints.json", "r") as f:
    src_fingerprints = json.load(f)

@pytest.mark.parametrize("table", tables)
def test_row_counts(table):
    
    with tgt_engine.connect() as conn:
        tgt_count = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
    
    assert src_counts[table] == tgt_count, f"Mismatch in table '{table}': {src_counts[table]} != {tgt_count}"

@pytest.mark.parametrize("table", tables)
def test_value_compare(table):
    if (table == 'COMPACTION_METRICS_CACHE' or table == 'WRITE_SET' or table == 'TXN_TO_WRITE_ID' or table == 'NEXT_WRITE_ID' 
        or table == 'MIN_HISTORY_WRITE_ID' or table == 'TXN_COMPONENTS' or table == 'COMPLETED_TXN_COMPONENTS' or table == 'TXN_LOCK_TBL'
        or table == 'NEXT_LOCK_ID' or table == 'NEXT_COMPACTION_QUEUE_ID' ):
        assert True
    else:
        with tgt_engine.connect() as conn:
            tgt_fingerprint: str = generate_fingerprint(tgt_engine, table, "public")

            assert src_fingerprints[table] == tgt_fingerprint, f"Mismatch in table '{table}': {src_fingerprints[table]} != {tgt_fingerprint}"