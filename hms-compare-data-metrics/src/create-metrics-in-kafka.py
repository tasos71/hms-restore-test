import pytest
import os
import time
from typing import Optional

from sqlalchemy import create_engine,text
from confluent_kafka import Producer
from confluent_kafka import avro
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import SerializationContext, MessageField
import argparse
import logging


TRINO_USER = os.getenv('TRINO_DB_USER', 'trino')
TRINO_PASSWORD = os.getenv('TRINO_DB_PASSWORD', '')
TRINO_HOST = os.getenv('TRINO_DB_HOST', 'localhost')
TRINO_PORT = os.getenv('TRINO_DB_PORT', '28082')
TRINO_CATALOG = os.getenv('TRINO_CATALOG', 'minio')
TRINO_SCHEMA = os.getenv('TRINO_SCHEMA', 'flight_db')

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_SECURITY_PROTOCOL = os.getenv('KAFKA_SECURITY_PROTOCOL', 'PLAINTEXT')
KAFKA_SSL_CA_LOCATION = os.getenv('KAFKA_SSL_CA', '/path/to/ca.pem')
KAFKA_SSL_CERT_LOCATION = os.getenv('KAFKA_SSL_CERT', '/path/to/client_cert.pem')
KAFKA_SSL_KEY_LOCATION = os.getenv('KAFKA_SSL_KEY', '/path/to/client_key.pem')
KAFKA_SSL_KEY_PASSWORD = os.getenv('KAFKA_SSL_KEY_PASSWORD', '')  # if your key is password protected
KAFKA_TOPIC_NAME = 'hms.table.metric.events.v1'
SCHEMA_REGISTRY_URL = os.getenv('SCHEMA_REGISTRY_URL', 'http://localhost:8081')


# Construct connection URLs
trino_url = f'trino://{TRINO_USER}:{TRINO_PASSWORD}@{TRINO_HOST}:{TRINO_PORT}/{TRINO_CATALOG}/{TRINO_SCHEMA}'

# Setup connections
trino_engine = create_engine(trino_url)

schema_registry_conf = {
    'url': SCHEMA_REGISTRY_URL  # change if needed
}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)
subject = KAFKA_TOPIC_NAME + "-value"

# Correct way to get schema - use get_latest_schema or get_version
try:
    # Option 1: Get specific version
    latest_schema = schema_registry_client.get_latest_version(subject)
    schema_str = latest_schema.schema.schema_str
except AttributeError:
    # Option 2: For older API versions
    schema_id = schema_registry_client.get_latest_schema(subject)[0]
    schema_str = schema_registry_client.get_latest_schema(subject)[1].schema_str


producer_config_plaintext = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'security.protocol': 'PLAINTEXT',
}

producer_config_ssl = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'security.protocol': 'SSL',
    'ssl.ca.location': KAFKA_SSL_CA_LOCATION,
    'ssl.certificate.location': KAFKA_SSL_CERT_LOCATION,
    'ssl.key.location': KAFKA_SSL_KEY_LOCATION,
    'ssl.key.password': KAFKA_SSL_KEY_PASSWORD
}

# Create AvroSerializer
avro_serializer = AvroSerializer(schema_registry_client, schema_str,to_dict=lambda obj, ctx: obj)

if KAFKA_SECURITY_PROTOCOL == 'SSL':
    producer = Producer(producer_config_ssl)
else:
    producer = Producer(producer_config_plaintext)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_count(table, timestamp_column=None):
    
    with trino_engine.connect() as conn:

        if timestamp_column:
            query = text(
                f'''
                SELECT 
                    COUNT(*) AS count, 
                    cast(to_unixtime(current_timestamp) AS bigint) * 1000 as execution_timestamp_ms, 
                    cast(to_unixtime(MAX({timestamp_column})) AS bigint) * 1000 as at_timestamp_ms
                FROM {table}
                '''
            )

            logger.debug(f"Executing query: {query}")
            count, execution_timestamp_ms, at_timestamp_ms = conn.execute(query).first()
        else:
            query = text(
                f'''
                SELECT 
                    COUNT(*) AS count, 
                    cast(to_unixtime(current_timestamp) AS bigint) * 1000 as execution_timestamp_ms 
                FROM {table}
                '''
            )
            logger.debug(f"Executing query: {query}")
            count, execution_timestamp_ms = conn.execute(query).first()
            at_timestamp_ms = None
    return count, execution_timestamp_ms, at_timestamp_ms

def create_metrics(table_name: str, timestamp_column: Optional[str] = None):
    count, execution_timestamp_ms, at_timestamp_ms = get_count(table_name, timestamp_column=timestamp_column)

    print (f"Producing count for {table_name}: {count} at {at_timestamp_ms}")

    # Create a message
    message = {
        'table_name': table_name,
        'event_time': at_timestamp_ms if at_timestamp_ms is not None else execution_timestamp_ms,  # use execution_timestamp_ms if at_timestamp_ms is None
        'value': count,
        'metric_type': 'count',
    }
        
    # Serialize the message using AvroSerializer
    serialized_message = avro_serializer(message, SerializationContext(KAFKA_TOPIC_NAME, MessageField.VALUE))

    # Produce the message to Kafka
    producer.produce(
            topic=KAFKA_TOPIC_NAME,
            value=serialized_message,
            key=table_name,  # we use the table as the key for the partitioning
            timestamp=at_timestamp_ms if at_timestamp_ms is not None else execution_timestamp_ms
    )

    producer.flush()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Produce metrics for a table to Kafka.")
    parser.add_argument("--table_name", required=True, help="Name of the table to process")
    parser.add_argument("--timestamp_column", required=False, help="Timestamp column name (optional)")

    args = parser.parse_args()
    table_name = args.table_name
    timestamp_column = args.timestamp_column

    create_metrics(table_name, timestamp_column=timestamp_column)      