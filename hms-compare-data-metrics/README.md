# Compare actual data to baseline table metics

## Prepare environment

```bash
python3.11 -m venv myenv
source venv/bin/activate

pip install -r requirements.txt
```

## Create metrics for a given table (with publishing to kafka)

```bash
export TRINO_USER=trino
export TRINO_PASSWORD=
export TRINO_HOST=localhost
export TRINO_PORT=28082
export TRINO_CATALOG=minio
export TRINO_SCHEMA=flight_db

# only needed it --publish_to_kafka is true
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export KAFKA_SECURITY_PROTOCOL=PLAINTEXT
export KAFKA_SSL_CA_LOCATION='/path/to/ca.pem'
export KAFKA_SSL_CERT_LOCATION='/path/to/client_cert.pem'
export KAFKA_SSL_KEY_LOCATION='/path/to/client_key.pem'
export KAFKA_SSL_KEY_PASSWORD=''
export KAFKA_TOPIC_NAME=hms.table.metric.events.v1
export SCHEMA_REGISTRY_URL=http://localhost:8081

python src/create-metrics-in-kafka.py --table_name=flights_0_t --timestamp_column=eventtimestamp --publish_to_kafka=true
```

## Consume from Kafka an compare against actual data

Set environment variables

```bash
export TRINO_USER=trino
export TRINO_PASSWORD=
export TRINO_HOST=localhost
export TRINO_PORT=28082

export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export KAFKA_SECURITY_PROTOCOL=PLAINTEXT
export KAFKA_SSL_CA_LOCATION='/path/to/ca.pem'
export KAFKA_SSL_CERT_LOCATION='/path/to/client_cert.pem'
export KAFKA_SSL_KEY_LOCATION='/path/to/client_key.pem'
export KAFKA_SSL_KEY_PASSWORD=''
export KAFKA_TOPIC_NAME=hms.table.metric.events.v1
export SCHEMA_REGISTRY_URL=http://localhost:8081
```


