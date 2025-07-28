import pytest
import os
import time
from sqlalchemy import create_engine,text
from confluent_kafka import Producer
from confluent_kafka import avro
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import SerializationContext, MessageField


TRINO_USER = os.getenv('TRINO_DB_USER', 'trino')
TRINO_PASSWORD = os.getenv('TRINO_DB_PASSWORD', '')
TRINO_HOST = os.getenv('TRINO_DB_HOST', 'localhost')
TRINO_PORT = os.getenv('TRINO_DB_PORT', '28082')
TRINO_SCHEMA = os.getenv('TRINO_SCHEMA', 'flight_db')

# Construct connection URLs
trino_url = f'trino://{TRINO_USER}:{TRINO_PASSWORD}@{TRINO_HOST}:{TRINO_PORT}/minio/{TRINO_SCHEMA}'

# Setup connections
trino_engine = create_engine(trino_url)

schema_registry_conf = {
    'url': 'http://localhost:8081'  # change if needed
}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

subject = 'hms.table.metric.events.v1-value'
version = 1

# Correct way to get schema - use get_latest_schema or get_version
try:
    # Option 1: Get specific version
    schema_metadata = schema_registry_client.get_version(subject, version)
    schema_str = schema_metadata.schema.schema_str
except AttributeError:
    # Option 2: For older API versions
    schema_id = schema_registry_client.get_latest_schema(subject)[0]
    schema_str = schema_registry_client.get_latest_schema(subject)[1].schema_str

print(schema_str)


# AvroProducer configuration
producer_config = {
    'bootstrap.servers': 'localhost:9092',
}

# Create AvroSerializer
avro_serializer = AvroSerializer(schema_registry_client, schema_str,to_dict=lambda obj, ctx: obj)

producer = Producer(producer_config)

def get_count(table, timestamp_column=None):
    
    with trino_engine.connect() as conn:

        if timestamp_column:
            query = text(f'SELECT COUNT(*) AS count, MAX({timestamp_column}) as at_timestamp FROM "{table}"')
            count, at_timestamp = conn.execute(query).first()
        else:
            query = text(f'SELECT COUNT(*) AS count FROM "{table}"')
            count = conn.execute(query).scalar()
            at_timestamp = None
    return count, at_timestamp

def produce_to_kafka():
    for table_num in range(10):
        table_name = f'flights_{table_num}_t'
        count, at_timestamp = get_count(table_name, timestamp_column='eventtimestamp')
        
        print (f"Producing count for {table_name}: {count} at {at_timestamp}")

        # Create a message
        message = {
            'table_name': table_name,
            'event_time': int(time.time() * 1000),  # current time in milliseconds
            'value': count,
            'metric_type': 'count',
        }
        
        # Serialize the message using AvroSerializer
        serialized_message = avro_serializer(message, SerializationContext('hms.table.metric.events.v1', MessageField.VALUE))
        
        # Produce the message to Kafka
        producer.produce(
            topic='hms.table.metric.events.v1', 
            value=serialized_message,
            key=table_name,  # we use the table as the key for the partitioning
            timestamp=int(time.time() * 1000)  # current system time in milliseconds
        )

produce_to_kafka()        