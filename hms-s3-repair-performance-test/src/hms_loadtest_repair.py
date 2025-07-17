import os
import docker
from sqlalchemy import create_engine,text
import timeit

from src import hms_loadtest_base

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

def loadtest_repair():        
    # Upload no repair the data
    for table_num in range(1, 1000):
        hms_loadtest_base.do_trino_repair(table_num)

loadtest_repair()
