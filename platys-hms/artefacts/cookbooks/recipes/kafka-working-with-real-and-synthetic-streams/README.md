---
technologies:       lakefs,minio
version:				1.19.0
validated-at:			3.7.2025
---

# Working with real and synthetic data streams

This recipe will show how to stream data into Kafka using various real and synthetic datastreams. 

## Initialise data platform

First [initialise a platys-supported data platform](../documentation/getting-started) with the following services enabled

```bash
export DATAPLATFORM_HOME=${PWD}
platys init --enable-services KAFKA,AKHQ,SCHEMA_REGISTRY,KAFKA_CONNECT -s trivadis/platys-modern-data-platform -w 1.19.0

platys gen
docker-compose up -d
```


## Bluesky

Create the Kafka topic

```bash
docker exec -ti kafka-1 kafka-topics --bootstrap-server kafka-1:19092 --create --topic bluesky.raw --replication-factor 3 --partitions 8
```

Run the bluesky retriever

```bash
<<<<<<< Updated upstream
docker run --name bluesky-retriever --rm -d -e DESTINATION=kafka -e KAFKA_BROKERS=192.168.1.112:9092 -e KAFKA_TOPIC=bluesky.raw ghcr.io/gschmutz/bluebird:latest
=======
docker run --name bluesky-retriever --rm -d -e DESTINATION=kafka -e KAFKA_BROKERS=10.156.72.251:9092 -e KAFKA_TOPIC=bluesky.raw ghcr.io/gschmutz/bluebird:latest
>>>>>>> Stashed changes
```

Let's see the messages comming in with `kcat` 

```bash
<<<<<<< Updated upstream
kcat -q -b 192.168.1.112:9092 -t bluesky.raw
=======
kcat -q -b 10.156.72.251:9092 -t bluesky.raw
>>>>>>> Stashed changes
```

What are the different message types?

```bash
<<<<<<< Updated upstream
kcat -q -b 192.168.1.112:9092 -t bluesky.raw | jq .record.commit.collection
=======
kcat -q -b 10.156.72.251:9092 -t bluesky.raw | jq .record.commit.collection
>>>>>>> Stashed changes
```

Let's view only the `text` of an `app.bsky.feed.post` message

```bash
<<<<<<< Updated upstream
kcat -q -b 192.168.1.112:9092 -t bluesky.raw | jq 'select(.record.commit.collection == "app.bsky.feed.post") | .record.commit.record.text'
=======
kcat -q -b 10.156.72.251:9092 -t bluesky.raw | jq 'select(.record.commit.collection == "app.bsky.feed.post") | .record.commit.record.text'
>>>>>>> Stashed changes
```

## Vehicles




   