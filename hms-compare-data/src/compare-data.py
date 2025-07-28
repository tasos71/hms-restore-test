import pytest
import os
import time
from sqlalchemy import create_engine,text
from confluent_kafka import Consumer, KafkaError, TopicPartition
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
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

# You can pass schema=None to use the schema from the Schema Registry
avro_deserializer = AvroDeserializer(schema_registry_client)

# Kafka Consumer config
consumer_conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'avro-consumer-group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True,
    'enable.partition.eof': True
}

def get_baseline_count(table):
    return latest_values[table]['value']

def get_actual_count(table):
    with trino_engine.connect() as conn:
        count = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
    return count

#@pytest.fixture(scope="session", autouse=True)
def init():
    latest_values = {}
    print ("running init")
    # read from kafka
    consumer = Consumer(consumer_conf)
    topic = 'hms.table.metric.events.v1'

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
def test_value_compare(table):

    baseline_count = get_baseline_count(table)
    actual_count = get_actual_count(table)

    assert baseline_count == actual_count, f"Mismatch in table '{table}': {baseline_count} != {actual_count}"