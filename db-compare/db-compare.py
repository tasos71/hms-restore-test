import pytest
import os
from sqlalchemy import create_engine,text

# Read connection details from environment variables
SRC_USER = os.getenv('SRC_DB_USER', 'hive')
SRC_PASSWORD = os.getenv('SRC_DB_PASSWORD', 'abc123!')
SRC_HOST = os.getenv('SRC_DB_HOST', 'localhost')
SRC_PORT = os.getenv('SRC_DB_PORT', '5442')
SRC_DBNAME = os.getenv('SRC_DB_NAME', 'metastore_db')

TGT_USER = os.getenv('TGT_DB_USER', 'hive')
TGT_PASSWORD = os.getenv('TGT_DB_PASSWORD', 'abc123!')
TGT_HOST = os.getenv('TGT_DB_HOST', 'localhost')
TGT_PORT = os.getenv('TGT_DB_PORT', '5442')
TGT_DBNAME = os.getenv('TGT_DB_NAME', 'metastore_db')

# Construct connection URLs
src_url = f'postgresql://{SRC_USER}:{SRC_PASSWORD}@{SRC_HOST}:{SRC_PORT}/{SRC_DBNAME}'
tgt_url = f'postgresql://{TGT_USER}:{TGT_PASSWORD}@{TGT_HOST}:{TGT_PORT}/{TGT_DBNAME}'

# Setup connections
src_engine = create_engine(src_url)
tgt_engine = create_engine(tgt_url)

# Table list to compare
#tables = ['CTLGS','DATABASE_PARAMS','DATACONNECTOR_PARAMS']

def get_table_names():
    with src_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_type = 'BASE TABLE'
        """))
        return [row[0] for row in result]

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
    with src_engine.connect() as conn:
        src_fingerprint = conn.execute(text(f"SELECT md5(string_agg(t::text, ',' ORDER BY rn)) AS fingerprint FROM (SELECT t.*, row_number() OVER () AS rn FROM \"{table}\" AS t) t")).scalar()

    with tgt_engine.connect() as conn:
        tgt_fingerprint = conn.execute(text(f"SELECT md5(string_agg(t::text, ',' ORDER BY rn)) AS fingerprint FROM (SELECT t.*, row_number() OVER () AS rn FROM \"{table}\" AS t) t")).scalar()

    assert src_fingerprint == tgt_fingerprint, f"Mismatch in table '{table}': {src_fingerprint} != {tgt_fingerprint}"