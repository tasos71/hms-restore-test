import pytest
import os
import time
from sqlalchemy import create_engine,text
from confluent_kafka import Consumer, KafkaError, TopicPartition
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField
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

# You can pass schema=None to use the schema from the Schema Registry
avro_deserializer = AvroDeserializer(schema_registry_client)

# Kafka Consumer config
consumer_conf_ssl = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'group.id': 'avro-consumer-group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True,
    'enable.partition.eof': True,
    'security.protocol': 'SSL',
    'ssl.ca.location': KAFKA_SSL_CA_LOCATION,
    'ssl.certificate.location': KAFKA_SSL_CERT_LOCATION,
    'ssl.key.location': KAFKA_SSL_KEY_LOCATION,
    'ssl.key.password': KAFKA_SSL_KEY_PASSWORD    
}

consumer_conf_plaintext = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'group.id': 'avro-consumer-group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True,
    'enable.partition.eof': True,
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_baseline(table):
    return latest_values[table]

def get_actual_count(table, timestamp_column=None, baseline_timestamp=None):
    """
    Retrieve the count of rows from a specified table over Trino, optionally filtered by a timestamp column and baseline timestamp.
    Please define the various environment variables for the connection to Trino including the catalog and schema.

    Args:
        table (str): The name of the table to query.
        timestamp_column (str, optional): The name of the timestamp column to filter by. If provided, the count will be filtered where the timestamp column is less than or equal to the baseline timestamp.
        baseline_timestamp (int or float, optional): The baseline timestamp (in Unix time) to use for filtering rows.

    Returns:
        int: The count of rows in the table, optionally filtered by the timestamp column and baseline timestamp.

    Raises:
        Exception: If there is an error executing the query.
    """


    with trino_engine.connect() as conn:

        if timestamp_column:
            query = text(
                f'''
                SELECT 
                    COUNT(*) AS count
                FROM {table}
                '''
            )

            logger.debug(f"Executing query: {query}")
            count = conn.execute(query).scalar()
        else:
            query = text(
                f'''
                SELECT 
                    COUNT(*) AS count
                FROM {table}
                WHERE {timestamp_column} <= from_unixtime({baseline_timestamp})
                '''
            )
            logger.debug(f"Executing query: {query}")
            count = conn.execute(query).scalar()
    return count

#@pytest.fixture(scope="session", autouse=True)
def init():
    latest_values = {}
    print ("running init")
    # read from kafka
    if KAFKA_SECURITY_PROTOCOL == 'SSL':
        consumer = Consumer(consumer_conf_ssl)
    else:
        consumer = Consumer(consumer_conf_plaintext)

    topic = KAFKA_TOPIC_NAME

    # Fetch metadata to get partition info
    metadata = consumer.list_topics(topic, timeout=10)
    partitions = metadata.topics[topic].partitions
    topic_partitions = [TopicPartition(topic, p) for p in partitions]

    consumer.assign(topic_partitions)

    time.sleep(2)  # wait for messages to be available
    
    # Seek to the beginning offset for each partition
    for tp in topic_partitions:
           consumer.seek(TopicPartition(topic, tp.partition, offset=0))

    try:
        print(f"Consuming messages from topic: {topic}")
        eof_count = 0
    
        while True:
            msg = consumer.poll(timeout = 2.0)
            if msg is None:
                continue
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print(f"Reached end of partition: {msg.topic()} [{msg.partition()}]")
                    eof_count += 1
                    # Optional: stop when all partitions have been consumed

                    print(f"EOF count: {eof_count}, Total partitions: {len(topic_partitions)}")

                    if eof_count == len(topic_partitions):
                        print("All partitions consumed.")
                        break
                else:                     
                    print("Consumer error: {}".format(msg.error()))
                    continue
            else:
                eof_count = 0
                # Deserialize the message using AvroDeserializer
                value = avro_deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))

                key = value.get('table_name')
                timestamp = value.get('event_time', 0)  # Assuming event_time is in milliseconds

                # Store only the latest value based on timestamp
                if key:
                    if key not in latest_values or timestamp > latest_values[key]['timestamp']:
                        latest_values[key] = {
                            'timestamp': timestamp,
                            'timestamp_column': value.get('timestamp_column', None),
                            'value': value.get('value', 0),
                            'metric_type': value.get('metric_type', ''),
                            'table_name': value.get('table_name', key)
                        }
                        print(f"Updated latest value for {key}: {latest_values[key]}")
                    else:
                        print(f"Skipped older message for {key}: timestamp {timestamp} <= {latest_values[key]['timestamp']}")

    except KeyboardInterrupt:
        print("Stopping consumer.")
    finally:
        consumer.close()
        print(f"Init completed. Found {len(latest_values)} tables: {list(latest_values.keys())}")
    return latest_values

latest_values = init()
tables = list(latest_values.keys())

@pytest.mark.parametrize("table", tables)
    """
    Test function to compare the value counts between baseline and actual data for a given table.

    This test is parameterized to run for each table in the `tables` list. For each table:
    - Retrieves the baseline count, timestamp column, and event time using `get_baseline`.
    - Retrieves the actual count from the target data source using `get_actual_count`, filtered by the timestamp column and baseline timestamp.
    - Asserts that the baseline and actual counts are equal, raising an assertion error with a descriptive message if they do not match.

    Args:
        table (str): The name of the table to compare.

    Raises:
        AssertionError: If the baseline count does not match the actual count for the given table.
    """
def test_value_compare(table):

    baseline_count = get_baseline(table)['value']
    timestamp_column = get_baseline(table)['timestamp_column']
    event_time = get_baseline(table)['timestamp']
    actual_count = get_actual_count(table, timestamp_column=timestamp_column, baseline_timestamp=event_time)

    assert baseline_count == actual_count, f"Mismatch in table '{table}': {baseline_count} != {actual_count}"