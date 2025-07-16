# Test Hive Metastore Backup & Restore

The following scenario will be tested by going through the steps documented below

![](./images/scenario.png)

## Preparation of environment

```bash
sudo rm -R backup
mkdir -p backup

docker compose down
docker volume prune -f

rm -R container-volume/minio/*
docker compose up -d
```

wait until Minio is available

```bash
docker exec -ti minio-mc mc rb minio-1/flight-bucket --force

docker exec -ti minio-mc mc mb minio-1/flight-bucket
docker exec -ti minio-mc mc version enable minio-1/flight-bucket

# verify that versioning works
docker exec -ti minio-mc mc version info minio-1/flight-bucket
```

Create the Kafka Audit Log topic

```bash
docker exec -ti kafka-1 kafka-topics --create --bootstrap-server kafka-1:19092 --topic minio-audit-log
docker exec -ti kafka-1 kafka-topics --create --bootstrap-server kafka-1:19092 --topic hms.notification.v1
```

**Create Hive Metastore Table**

```bash
docker exec -ti hive-metastore hive
```

you need to connect to `hive-server` if on **Hive Metastore 4.0.1**

```
!connect jdbc:hive2://hive-server:10000
```

or through hive-server if on **Hive Metastore 4.0.1**

```bash
docker exec -ti hive-server beeline -u jdbc:hive2://hive-server:10000
```

```sql
CREATE DATABASE flight_db
LOCATION 's3a://flight-bucket/';

USE flight_db;

DROP TABLE IF EXISTS airport_t;
CREATE EXTERNAL TABLE airport_t (id int
                                , ident string
                                , type string
                                , name string
                                , latitude_deg double
                                , longitude_deg double
                                , elevation_ft int
                                , continent string
                                , iso_country string
                                , iso_region string
                                , municipality string
                                , scheduled_service string
                                , gps_code string
                                , iata_code string
                                , local_code string
                                , home_link string
                                , wikipedia_link string
                                , keywords string
                                )
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  "separatorChar" = ",",
  "quoteChar"     = "\""
)
STORED AS TEXTFILE
LOCATION 's3a://flight-bucket/raw/airports'
TBLPROPERTIES (
  "skip.header.line.count" = "1"
);

DROP TABLE IF EXISTS flights_t;
CREATE EXTERNAL TABLE flights_t ( dayOfMonth integer
                             , dayOfWeek integer
                             , depTime integer
                             , crsDepTime integer
                             , arrTime integer
                             , crsArrTime integer
                             , uniqueCarrier string
                             , flightNum string
                             , tailNum string
                             , actualElapsedTime integer
                             , crsElapsedTime integer
                             , airTime integer
                             , arrDelay integer
                             , depDelay integer
                             , origin string
                             , destination string
                             , distance integer) 
PARTITIONED BY (year integer, month integer)
STORED AS parquet
LOCATION 's3a://flight-bucket/refined/flights';

!quit
```

Using Trino

```sql
CREATE SCHEMA minio.flight_db;

DROP TABLE IF EXISTS minio.flight_db.airport_t;

CREATE TABLE minio.flight_db.airport_t (
    id               VARCHAR,
    ident            VARCHAR,
    type             VARCHAR,
    name             VARCHAR,
    latitude_deg     VARCHAR,
    longitude_deg    VARCHAR,
    elevation_ft     VARCHAR,
    continent        VARCHAR,
    iso_country      VARCHAR,
    iso_region       VARCHAR,
    municipality     VARCHAR,
    scheduled_service VARCHAR,
    gps_code         VARCHAR,
    iata_code        VARCHAR,
    local_code       VARCHAR,
    home_link        VARCHAR,
    wikipedia_link   VARCHAR,
    keywords         VARCHAR
)
WITH (
    external_location = 's3a://flight-bucket/raw/airports/',
    format = 'CSV',
    skip_header_line_count = 1
);

DROP TABLE IF EXISTS minio.flight_db.flights_t;

CREATE TABLE minio.flight_db.flights_t (
    dayOfMonth         INTEGER,
    dayOfWeek          INTEGER,
    depTime            INTEGER,
    crsDepTime         INTEGER,
    arrTime            INTEGER,
    crsArrTime         INTEGER,
    uniqueCarrier      VARCHAR,
    flightNum          VARCHAR,
    tailNum            VARCHAR,
    actualElapsedTime  INTEGER,
    crsElapsedTime     INTEGER,
    airTime            INTEGER,
    arrDelay           INTEGER,
    depDelay           INTEGER,
    origin             VARCHAR,
    destination        VARCHAR,
    distance           INTEGER,
    year               INTEGER,
    month              INTEGER
)
WITH (
    external_location = 's3a://flight-bucket/refined/flights/',
    format = 'PARQUET',
    partitioned_by = ARRAY['year', 'month']
);
```

**Check the HMS Notification Log**

```bash
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select nl_id, event_id, event_type, from_unixtime(event_time) from hive_metastore_db.public.notification_log" 
```

```bash
guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select nl_id, event_id, event_type, from_unixtime(event_time) from hive_metastore_db.public.notification_log"

"1","1","CREATE_DATABASE","2025-06-26 15:15:20.000 UTC"
"2","2","CREATE_TABLE","2025-06-26 15:15:21.000 UTC"
"3","3","CREATE_TABLE","2025-06-26 15:15:24.000 UTC"
```

## Handle period 1

```bash
docker exec -ti minio-mc mc cp /data-transfer/airport-data/airports-1.csv minio-1/flight-bucket/raw/airports/airports.csv
```

```bash
docker exec -ti minio-mc mc cp --recursive /data-transfer/flight-data/flights-medium-parquet-partitioned/flights/year=2008/month=1 minio-1/flight-bucket/refined/flights/year=2008/
```

* Execute this if **using Hive Metastore < 4.0.1**

```bash
docker exec -ti hive-metastore hive -e 'MSCK REPAIR TABLE flight_db.flights_t;'
```

```
guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti hive-metastore hive -e 'MSCK REPAIR TABLE flight_db.flights_t;'
SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/opt/hive/lib/log4j-slf4j-impl-2.17.1.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/opt/hadoop/share/hadoop/common/lib/slf4j-log4j12-1.7.25.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]
Hive Session ID = fa9533e9-5152-4421-8da7-9e16fb040591
OK
Partitions not in metastore:	flights_t:year=2008/month=1
Repair: Added partition to metastore flights_t:year=2008/month=1
Time taken: 3.043 seconds, Fetched: 2 row(s)
```


* Execute this if **using Metastore 4.0.1** with [**Trino 351+**](https://trino.io/docs/current/connector/hive.html#procedures)

```bash
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "call minio.system.sync_partition_metadata('flight_db', 'flights_t', 'FULL')"
```

**Check the HMS Notification Log**

```bash
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select nl_id, event_id, event_type, from_unixtime(event_time) from hive_metastore_db.public.notification_log" 
```

```bash
guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select nl_id, event_id, event_type, from_unixtime(event_time) from hive_metastore_db.public.notification_log"
"1","1","CREATE_DATABASE","2025-06-26 15:15:20.000 UTC"
"2","2","CREATE_TABLE","2025-06-26 15:15:21.000 UTC"
"3","3","CREATE_TABLE","2025-06-26 15:15:24.000 UTC"
"4","4","ADD_PARTITION","2025-06-26 15:17:53.000 UTC"
```

**Check with Trino**

```sql
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select count(*) from minio.flight_db.airport_t" 
```

returns `999`

```sql
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select count(*) from minio.flight_db.flights_t" 
```

returns `605765`

**Backup Minio**

```bash
cp -R container-volume/minio/ backup/1
```

## Handle period 2

**Backup Hive Metastore (A)**

```bash
docker exec -t hive-metastore-db pg_dump -U hive -d metastore_db -F c -f /hms-A.dump
docker cp hive-metastore-db:/hms-A.dump ./backup
```

```bash
docker exec -ti minio-mc mc cp /data-transfer/airport-data/airports-2.csv minio-1/flight-bucket/raw/airports/airports.csv
```

```bash
docker exec -ti minio-mc mc cp --recursive /data-transfer/flight-data/flights-medium-parquet-partitioned/flights/year=2008/month=2 minio-1/flight-bucket/refined/flights/year=2008/
```

* Execute this if **using Hive Metastore < 4.0.1**

```bash
docker exec -ti hive-metastore hive -e 'MSCK REPAIR TABLE flight_db.flights_t;'
```

```bash
guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti hive-metastore hive -e 'MSCK REPAIR TABLE flight_db.flights_t;'
SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/opt/hive/lib/log4j-slf4j-impl-2.17.1.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/opt/hadoop/share/hadoop/common/lib/slf4j-log4j12-1.7.25.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]
Hive Session ID = b85c9448-446e-4e3c-8da6-c51f7d11911f

Logging initialized using configuration in file:/opt/hive/conf/hive-log4j2.properties Async: true
Hive Session ID = dc5e88e0-eb20-41c3-b518-a14d21e9ed34
OK
Partitions not in metastore:	flights_t:year=2008/month=2
Repair: Added partition to metastore flights_t:year=2008/month=2
Time taken: 2.943 seconds, Fetched: 2 row(s)
```

* Execute this if **using Metastore 4.0.1** with [**Trino 351+**](https://trino.io/docs/current/connector/hive.html#procedures)

```bash
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "call minio.system.sync_partition_metadata('flight_db', 'flights_t', 'FULL')"
```

**Check the HMS Notification Log**

```bash
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select nl_id, event_id, event_type, from_unixtime(event_time) from hive_metastore_db.public.notification_log" 
```

```bash
guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select nl_id, event_id, event_type, from_unixtime(event_time) from hive_metastore_db.public.notification_log"
"1","1","CREATE_DATABASE","2025-06-26 09:53:28.000 UTC"
"2","2","CREATE_TABLE","2025-06-26 09:53:29.000 UTC"
"3","3","CREATE_TABLE","2025-06-26 09:53:32.000 UTC"
"4","4","ADD_PARTITION","2025-06-26 09:53:34.000 UTC"
"5","5","ADD_PARTITION","2025-06-26 09:54:43.000 UTC"
```

**Check with Trino** 

```
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select count(*) from minio.flight_db.airport_t" 
```

returns `1240`

```sql
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select count(*) from minio.flight_db.flights_t" 
```

returns `1175001`

**Create a new table based on the exising `flights_t` table**

```bash
docker exec -ti hive-metastore hive
```

you need to connect to `hive-server` if on **Hive Metastore 4.0.1**

```
!connect jdbc:hive2://hive-server:10000
```

or through hive-server if on **Hive Metastore 4.0.1**

```bash
docker exec -ti hive-server beeline -u jdbc:hive2://hive-server:10000
```

```sql
use flight_db;

CREATE EXTERNAL TABLE flights_per_carrier_t (
  uniquecarrier STRING,
  flight_count BIGINT
)
STORED AS PARQUET
LOCATION 's3a://flight-bucket/refined/flights-per-carrier';

!quit
```

```sql
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "INSERT INTO minio.flight_db.flights_per_carrier_t SELECT uniquecarrier, COUNT(*) AS flight_count FROM minio.flight_db.flights_t GROUP BY uniquecarrier" 
```

**Check with Trino** 

```sql
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select count(*) from minio.flight_db.flights_per_carrier_t" 
```

returns `20`

**Check the HMS Notification Log**

```bash
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select nl_id, event_id, event_type, from_unixtime(event_time) from hive_metastore_db.public.notification_log" 
```

```bash
guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select nl_id, event_id, event_type, from_unixtime(event_time) from hive_metastore_db.public.notification_log"
"1","1","CREATE_DATABASE","2025-06-26 09:53:28.000 UTC"
"2","2","CREATE_TABLE","2025-06-26 09:53:29.000 UTC"
"3","3","CREATE_TABLE","2025-06-26 09:53:32.000 UTC"
"4","4","ADD_PARTITION","2025-06-26 09:53:34.000 UTC"
"5","5","ADD_PARTITION","2025-06-26 09:54:43.000 UTC"
"6","6","CREATE_TABLE","2025-06-26 09:55:42.000 UTC"
"7","7","ALTER_TABLE","2025-06-26 09:55:53.000 UTC"
```

**Backup Minio**

```bash
cp -R container-volume/minio/ backup/2
```

## Handle period 3

**Upload `flights`**

```bash
docker exec -ti minio-mc mc cp --recursive /data-transfer/flight-data/flights-medium-parquet-partitioned/flights/year=2008/month=3 minio-1/flight-bucket/refined/flights/year=2008/
```

* Execute this if **using Hive Metastore < 4.0.1**

```bash
docker exec -ti hive-metastore hive -e 'MSCK REPAIR TABLE flight_db.flights_t;'
```

* Execute this if **using Metastore 4.0.1** with [**Trino 351+**](https://trino.io/docs/current/connector/hive.html#procedures)

```bash
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "call minio.system.sync_partition_metadata('flight_db', 'flights_t', 'FULL')"
```

**Backup Hive Metastore (B)**

```bash
docker exec -t hive-metastore-db pg_dump -U hive -d metastore_db -F c -f /hms-B.dump
docker cp hive-metastore-db:/hms-B.dump ./backup
```

**Upload `airports`**

```bash
docker exec -ti minio-mc mc cp /data-transfer/airport-data/airports-3.csv minio-1/flight-bucket/raw/airports/airports.csv
```

```bash
guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti hive-metastore hive -e 'MSCK REPAIR TABLE flight_db.flights_t;'
SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/opt/hive/lib/log4j-slf4j-impl-2.17.1.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/opt/hadoop/share/hadoop/common/lib/slf4j-log4j12-1.7.25.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]
Hive Session ID = 1e53fba8-24a1-4bef-881c-63a61151d00e

Logging initialized using configuration in file:/opt/hive/conf/hive-log4j2.properties Async: true
Hive Session ID = 6a3175c5-4e46-49e8-bf30-fc1ac459280a
OK
Partitions not in metastore:	flights_t:year=2008/month=3
Repair: Added partition to metastore flights_t:year=2008/month=3
Time taken: 2.827 seconds, Fetched: 2 row(s)
```

**Check the HMS Notification Log**

```bash
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select nl_id, event_id, event_type, from_unixtime(event_time) from hive_metastore_db.public.notification_log" 
```

```
guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select nl_id, event_id, event_type from hive_metastore_db.public.notification_log"
"1","1","CREATE_DATABASE","2025-06-26 09:53:28.000 UTC"
"2","2","CREATE_TABLE","2025-06-26 09:53:29.000 UTC"
"3","3","CREATE_TABLE","2025-06-26 09:53:32.000 UTC"
"4","4","ADD_PARTITION","2025-06-26 09:53:34.000 UTC"
"5","5","ADD_PARTITION","2025-06-26 09:54:43.000 UTC"
"6","6","CREATE_TABLE","2025-06-26 09:55:42.000 UTC"
"7","7","ALTER_TABLE","2025-06-26 09:55:53.000 UTC"
"8","8","ADD_PARTITION","2025-06-26 09:57:13.000 UTC"
```

**Check with Trino**

```
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select count(*) from minio.flight_db.airport_t" 
```

returns `2150`

```sql
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select count(*) from minio.flight_db.flights_t" 
```

returns `1791091`

**Backup Minio**

```bash
cp -R container-volume/minio/ backup/3
```

## Handle period 4

**Backup Hive Metastore (C)**

```bash
docker exec -t hive-metastore-db pg_dump -U hive -d metastore_db -F c -f /hms-C.dump
docker cp hive-metastore-db:/hms-C.dump ./backup
```

```bash
docker exec -ti minio-mc mc cp /data-transfer/airport-data/airports-4.csv minio-1/flight-bucket/raw/airports/airports.csv
```

List the versions of an object

```bash
docker exec -ti minio-mc mc ls --versions minio-1/flight-bucket/raw/airports/airports.csv
```

```bash
docker exec -ti minio-mc mc cp --recursive /data-transfer/flight-data/flights-medium-parquet-partitioned/flights/year=2008/month=4 minio-1/flight-bucket/refined/flights/year=2008/
```

* Execute this if **using Hive Metastore < 4.0.1**

```bash
docker exec -ti hive-metastore hive -e 'MSCK REPAIR TABLE flight_db.flights_t;'
```

```
guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti hive-metastore hive -e 'MSCK REPAIR TABLE guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti hive-metastore hive -e 'MSCK REPAIR TABLE flight_db.flights_t;'
SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/opt/hive/lib/log4j-slf4j-impl-2.17.1.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/opt/hadoop/share/hadoop/common/lib/slf4j-log4j12-1.7.25.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]
Hive Session ID = ce3f3db9-9c7c-4504-aa75-2b33da3e88db

Logging initialized using configuration in file:/opt/hive/conf/hive-log4j2.properties Async: true
Hive Session ID = 5cde7a6b-cf73-4a7b-bbf0-e808798fc4a2
OK
Partitions not in metastore:	flights_t:year=2008/month=4
Repair: Added partition to metastore flights_t:year=2008/month=4
Time taken: 2.969 seconds, Fetched: 2 row(s)
```

* Execute this if **using Metastore 4.0.1** with [**Trino 351+**](https://trino.io/docs/current/connector/hive.html#procedures)

```bash
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "call minio.system.sync_partition_metadata('flight_db', 'flights_t', 'FULL')"
```

**Check the HMS Notification Log**

```bash
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select nl_id, event_id, event_type, from_unixtime(event_time) from hive_metastore_db.public.notification_log" 
```

```
guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select nl_id, event_id, event_type, from_unixtime(event_time) from hive_metastore_db.public.notification_log"

"1","1","CREATE_DATABASE","2025-06-26 15:15:20.000 UTC"
"2","2","CREATE_TABLE","2025-06-26 15:15:21.000 UTC"
"3","3","CREATE_TABLE","2025-06-26 15:15:24.000 UTC"
"4","4","ADD_PARTITION","2025-06-26 15:17:53.000 UTC"
"5","5","ADD_PARTITION","2025-06-26 15:21:57.000 UTC"
"6","6","CREATE_TABLE","2025-06-26 15:23:06.000 UTC"
"7","7","ALTER_TABLE","2025-06-26 15:23:17.000 UTC"
"8","8","ADD_PARTITION","2025-06-26 15:25:07.000 UTC"
"9","9","ADD_PARTITION","2025-06-26 15:31:19.000 UTC"
```

**Check with Trino**

```bash
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select count(*) from minio.flight_db.airport_t" 
```

returns `81193`

```sql
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select count(*) from minio.flight_db.flights_t" 
```

returns `2389217`

**Backup Minio & Hive Metastore**

```bash
cp -R container-volume/minio/ backup/4
```

## Handle Period 5

**Backup Hive Metastore (D)**

```bash
docker exec -t hive-metastore-db pg_dump -U hive -d metastore_db -F c -f /hms-D.dump
docker cp hive-metastore-db:/hms-D.dump ./backup
```

```bash
docker cp hive-metastore-db:/hms-A.dump ./backup
docker cp hive-metastore-db:/hms-B.dump ./backup
docker cp hive-metastore-db:/hms-C.dump ./backup
docker cp hive-metastore-db:/hms-D.dump ./backup
```

## Rollback Minio to end of Period 2

Let's rollback MinIO to the backup of the end Period 2


```bash
docker stop minio-1 && docker rm minio-1

rm -R container-volume/minio/*
cp -R backup/2/* container-volume/minio

docker compose up -d
```

List the versions of an object

```bash
docker exec -ti minio-mc mc ls --versions minio-1/flight-bucket/raw/airports/airports.csv
```

```bash
guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti minio-mc mc ls --versions minio-1/flight-bucket/raw/airports/airports.csv
[2025-06-26 13:10:19 UTC] 169KiB STANDARD 6ddf4f7a-fe17-4f86-a4f7-4513ee22dd4a v2 PUT airports.csv
[2025-06-26 13:08:09 UTC] 136KiB STANDARD 435c2577-f96d-4a05-8af1-256d0e0cb90e v1 PUT airports.csv
```

```bash
docker exec -ti minio-mc mc tree --files  minio-1/flight-bucket/refined/flights
```

```bash
guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti minio-mc mc tree --files  minio-1/flight-bucket/refined/flights
minio-1/flight-bucket/refined/flights
└─ year=2008
   ├─ month=1
   │  ├─ part-00000-8e3379b7-ffe4-4904-a252-c471bf253208.c000.snappy.parquet
   │  ├─ part-00001-8e3379b7-ffe4-4904-a252-c471bf253208.c000.snappy.parquet
   │  ├─ part-00002-8e3379b7-ffe4-4904-a252-c471bf253208.c000.snappy.parquet
   │  ├─ part-00003-8e3379b7-ffe4-4904-a252-c471bf253208.c000.snappy.parquet
   │  ├─ part-00004-8e3379b7-ffe4-4904-a252-c471bf253208.c000.snappy.parquet
   │  ├─ part-00005-8e3379b7-ffe4-4904-a252-c471bf253208.c000.snappy.parquet
   │  ├─ part-00006-8e3379b7-ffe4-4904-a252-c471bf253208.c000.snappy.parquet
   │  ├─ part-00007-8e3379b7-ffe4-4904-a252-c471bf253208.c000.snappy.parquet
   │  ├─ part-00008-8e3379b7-ffe4-4904-a252-c471bf253208.c000.snappy.parquet
   │  └─ part-00009-8e3379b7-ffe4-4904-a252-c471bf253208.c000.snappy.parquet
   └─ month=2
      ├─ part-00000-2b462dad-0a94-47a4-81fa-6115c3f7d62f.c000.snappy.parquet
      ├─ part-00001-2b462dad-0a94-47a4-81fa-6115c3f7d62f.c000.snappy.parquet
      ├─ part-00002-2b462dad-0a94-47a4-81fa-6115c3f7d62f.c000.snappy.parquet
      ├─ part-00003-2b462dad-0a94-47a4-81fa-6115c3f7d62f.c000.snappy.parquet
      ├─ part-00004-2b462dad-0a94-47a4-81fa-6115c3f7d62f.c000.snappy.parquet
      ├─ part-00005-2b462dad-0a94-47a4-81fa-6115c3f7d62f.c000.snappy.parquet
      ├─ part-00006-2b462dad-0a94-47a4-81fa-6115c3f7d62f.c000.snappy.parquet
      ├─ part-00007-2b462dad-0a94-47a4-81fa-6115c3f7d62f.c000.snappy.parquet
      ├─ part-00008-2b462dad-0a94-47a4-81fa-6115c3f7d62f.c000.snappy.parquet
      └─ part-00009-2b462dad-0a94-47a4-81fa-6115c3f7d62f.c000.snappy.parquet
```

* if on **Hive Metastore < 4.0.1**

```bash
docker exec -ti hive-metastore hive -e 'SHOW PARTITIONS flight_db.flights_t;'
```

```bash
guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti hive-metastore hive -e 'SHOW PARTITIONS flight_db.flights_t;'
SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/opt/hive/lib/log4j-slf4j-impl-2.17.1.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/opt/hadoop/share/hadoop/common/lib/slf4j-log4j12-1.7.25.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]
Hive Session ID = 7452bd69-b2d4-4094-9de8-e8293130d799

Logging initialized using configuration in file:/opt/hive/conf/hive-log4j2.properties Async: true
Hive Session ID = b063d497-a906-4d85-b4b2-db0682ff10e0
OK
year=2008/month=1
year=2008/month=2
year=2008/month=3
year=2008/month=4
Time taken: 1.006 seconds, Fetched: 4 row(s)
```

A repair shows the 2 partitions which do no exists at the end of Period 2.

```bash
docker exec -ti hive-metastore hive -e 'MSCK REPAIR TABLE flight_db.flights_t;'
```

```
guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti hive-metastore hive -e 'MSCK REPAIR TABLE flight_db.flights_t;'
SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/opt/hive/lib/log4j-slf4j-impl-2.17.1.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/opt/hadoop/share/hadoop/common/lib/slf4j-log4j12-1.7.25.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]
Hive Session ID = d8d1a525-007e-476b-a29d-08d501e98b56

Logging initialized using configuration in file:/opt/hive/conf/hive-log4j2.properties Async: true
Hive Session ID = f3da186c-a690-44a4-a2bb-a3be1fe55bba
OK
Partitions missing from filesystem:	flights_t:year=2008/month=3	flights_t:year=2008/month=4
Time taken: 2.605 seconds, Fetched: 1 row(s)
```

* if on **Hive Metastore 4.0.1**

or through hive-server if on **Hive Metastore 4.0.1**

```bash
docker exec -ti hive-server beeline -u jdbc:hive2://hive-server:10000 -e "SHOW PARTITIONS flight_db.flights_t;"
```

```bash
docker exec -ti hive-server beeline -u jdbc:hive2://hive-server:10000 -e "SHOW PARTITIONS flight_db.flights_t;"
INFO  : Compiling command(queryId=hive_20250703085508_7c57cc71-bf87-4e12-9014-12c1d5d25809): SHOW PARTITIONS flight_db.flights_t
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Semantic Analysis Completed (retrial = false)
INFO  : Returning Hive schema: Schema(fieldSchemas:[FieldSchema(name:partition, type:string, comment:from deserializer)], properties:null)
INFO  : Completed compiling command(queryId=hive_20250703085508_7c57cc71-bf87-4e12-9014-12c1d5d25809); Time taken: 0.285 seconds
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Executing command(queryId=hive_20250703085508_7c57cc71-bf87-4e12-9014-12c1d5d25809): SHOW PARTITIONS flight_db.flights_t
INFO  : Starting task [Stage-0:DDL] in serial mode
INFO  : Completed executing command(queryId=hive_20250703085508_7c57cc71-bf87-4e12-9014-12c1d5d25809); Time taken: 0.056 seconds
INFO  : OK
INFO  : Concurrency mode is disabled, not creating a lock manager
+--------------------+
|     partition      |
+--------------------+
| year=2008/month=1  |
| year=2008/month=2  |
| year=2008/month=3  |
| year=2008/month=4  |
+--------------------+
4 rows selected (0.823 seconds)
```

if we use Trino to sync partition metadata with the `FULL` option, the no-existing partitions are removed

```bash
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "call minio.system.sync_partition_metadata('flight_db', 'flights_t', 'FULL')"
```

Which we can check by rerunning the `SHOW PARTITIONS` command again

```bash
docker exec -ti hive-server beeline -u jdbc:hive2://hive-server:10000 -e "SHOW PARTITIONS flight_db.flights_t;"
```

```bash
guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/platys-hms (main)> docker exec -ti hive-server beeline -u jdbc:hive2://hive-server:10000 -e "SHOW PARTITIONS flight_db.flights_t;"

SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/opt/hive/lib/log4j-slf4j-impl-2.17.1.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/opt/hadoop/share/hadoop/common/lib/slf4j-log4j12-1.7.25.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]
Connecting to jdbc:hive2://hive-server:10000
Connected to: Apache Hive (version 3.1.3)
Driver: Hive JDBC (version 3.1.3)
Transaction isolation: TRANSACTION_REPEATABLE_READ
INFO  : Compiling command(queryId=hive_20250703085845_df5b167a-cae5-432d-abbe-ff3a1951e891): SHOW PARTITIONS flight_db.flights_t
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Semantic Analysis Completed (retrial = false)
INFO  : Returning Hive schema: Schema(fieldSchemas:[FieldSchema(name:partition, type:string, comment:from deserializer)], properties:null)
INFO  : Completed compiling command(queryId=hive_20250703085845_df5b167a-cae5-432d-abbe-ff3a1951e891); Time taken: 0.066 seconds
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Executing command(queryId=hive_20250703085845_df5b167a-cae5-432d-abbe-ff3a1951e891): SHOW PARTITIONS flight_db.flights_t
INFO  : Starting task [Stage-0:DDL] in serial mode
INFO  : Completed executing command(queryId=hive_20250703085845_df5b167a-cae5-432d-abbe-ff3a1951e891); Time taken: 0.032 seconds
INFO  : OK
INFO  : Concurrency mode is disabled, not creating a lock manager
+--------------------+
|     partition      |
+--------------------+
| year=2008/month=1  |
| year=2008/month=2  |
+--------------------+
2 rows selected (0.244 seconds)
Beeline version 3.1.3 by Apache Hive
[WARN] Failed to create directory: /home/hive/.beeline
No such file or directory
Closing: 0: jdbc:hive2://hive-server:10000
```

## Rollback HMS to Snapshot A

```bash
docker stop hive-metastore-db && docker rm hive-metastore-db

docker compose up -d
```

```bash
docker cp backup/hms-A.dump hive-metastore-db:/
docker exec -i hive-metastore-db pg_restore -U hive -d metastore_db /hms-A.dump
```

```bash
docker restart hive-metastore
```

* if on **Hive Metastore < 4.0.1**

```
docker exec -ti hive-metastore hive -e 'show partitions flight_db.flights_t;'
```

```bash
guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti hive-metastore hive -e 'show partitions flight_db.flights_t;'
SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/opt/hive/lib/log4j-slf4j-impl-2.17.1.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/opt/hadoop/share/hadoop/common/lib/slf4j-log4j12-1.7.25.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]
Hive Session ID = 49637913-9e6e-4448-922f-cc6a61647e6a

Logging initialized using configuration in file:/opt/hive/conf/hive-log4j2.properties Async: true
Hive Session ID = 0bae7e39-df60-4e6d-bd49-1df68e9aa164
OK
year=2008/month=1
Time taken: 1.205 seconds, Fetched: 1 row(s)
```

* if on **Hive Metastore 4.0.1**

```bash
docker exec -ti hive-server beeline -u jdbc:hive2://hive-server:10000 -e "SHOW PARTITIONS flight_db.flights_t;"
```

```bash
INFO  : Compiling command(queryId=hive_20250703090241_8c82da32-c9e5-49c1-bd42-ca6836a28301): SHOW PARTITIONS flight_db.flights_t
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Semantic Analysis Completed (retrial = false)
INFO  : Returning Hive schema: Schema(fieldSchemas:[FieldSchema(name:partition, type:string, comment:from deserializer)], properties:null)
INFO  : Completed compiling command(queryId=hive_20250703090241_8c82da32-c9e5-49c1-bd42-ca6836a28301); Time taken: 0.326 seconds
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Executing command(queryId=hive_20250703090241_8c82da32-c9e5-49c1-bd42-ca6836a28301): SHOW PARTITIONS flight_db.flights_t
INFO  : Starting task [Stage-0:DDL] in serial mode
INFO  : Completed executing command(queryId=hive_20250703090241_8c82da32-c9e5-49c1-bd42-ca6836a28301); Time taken: 0.079 seconds
INFO  : OK
INFO  : Concurrency mode is disabled, not creating a lock manager
+--------------------+
|     partition      |
+--------------------+
| year=2008/month=1  |
+--------------------+
1 row selected (0.582 seconds)
```

**Check with Trino**

```
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select count(*) from minio.flight_db.airport_t"
```

returns `1240`

```sql
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select count(*) from minio.flight_db.flights_t" 
```

returns `605765`

Repair the table

* if on **Hive Metastore < 4.0.1**

```bash
docker exec -ti hive-metastore hive -e 'MSCK REPAIR TABLE flight_db.flights_t;'
```

```bash
guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti hive-metastore hive -e 'MSCK REPAIR TABLE flight_db.flights_t;'

SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/opt/hive/lib/log4j-slf4j-impl-2.17.1.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/opt/hadoop/share/hadoop/common/lib/slf4j-log4j12-1.7.25.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]
Hive Session ID = bc98ea95-8749-4ccf-ae69-0160b24881ea

Logging initialized using configuration in file:/opt/hive/conf/hive-log4j2.properties Async: true
Hive Session ID = bfcb7c3c-9cc5-48c9-8131-fbc1af45ac80
OK
Partitions not in metastore:	flights_t:year=2008/month=2
Repair: Added partition to metastore flights_t:year=2008/month=2
Time taken: 4.73 seconds, Fetched: 2 row(s)
```

* if on **Hive Metastore 4.0.1**

if we use Trino to sync partition metadata with the `FULL` option, the no-existing partitions are removed

```bash
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "call minio.system.sync_partition_metadata('flight_db', 'flights_t', 'FULL')"
```


```bash
docker exec -ti hive-server beeline -u jdbc:hive2://hive-server:10000 -e "SHOW PARTITIONS flight_db.flights_t;"
```

```bash
Connecting to jdbc:hive2://hive-server:10000
Connected to: Apache Hive (version 3.1.3)
Driver: Hive JDBC (version 3.1.3)
Transaction isolation: TRANSACTION_REPEATABLE_READ
INFO  : Compiling command(queryId=hive_20250703090552_35217268-2819-48d5-a457-c7c92f8a34f9): SHOW PARTITIONS flight_db.flights_t
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Semantic Analysis Completed (retrial = false)
INFO  : Returning Hive schema: Schema(fieldSchemas:[FieldSchema(name:partition, type:string, comment:from deserializer)], properties:null)
INFO  : Completed compiling command(queryId=hive_20250703090552_35217268-2819-48d5-a457-c7c92f8a34f9); Time taken: 0.1 seconds
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Executing command(queryId=hive_20250703090552_35217268-2819-48d5-a457-c7c92f8a34f9): SHOW PARTITIONS flight_db.flights_t
INFO  : Starting task [Stage-0:DDL] in serial mode
INFO  : Completed executing command(queryId=hive_20250703090552_35217268-2819-48d5-a457-c7c92f8a34f9); Time taken: 0.052 seconds
INFO  : OK
INFO  : Concurrency mode is disabled, not creating a lock manager
+--------------------+
|     partition      |
+--------------------+
| year=2008/month=1  |
| year=2008/month=2  |
+--------------------+
```


**Check with Trino**

```
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select count(*) from minio.flight_db.airport_t"
```

returns `1240`

```sql
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select count(*) from minio.flight_db.flights_t" 
```

returns `1175001`


## Rollback HMS to Snapshot B

```bash
docker stop hive-metastore-db && docker rm hive-metastore-db

docker compose up -d
```

```bash
docker cp backup/hms-B.dump hive-metastore-db:/
docker exec -i hive-metastore-db pg_restore -U hive -d metastore_db /hms-B.dump
```

```bash
docker restart hive-metastore
```

* if on **Hive Metastore < 4.0.1**

```
docker exec -ti hive-metastore hive -e 'show partitions flight_db.flights_t;'
```

```bash
guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti hive-metastore hive -e 'show partitions flight_db.flights_t;'
SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/opt/hive/lib/log4j-slf4j-impl-2.17.1.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/opt/hadoop/share/hadoop/common/lib/slf4j-log4j12-1.7.25.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]
Hive Session ID = 0ba92976-04f2-464d-a323-5a815991a9ba

Logging initialized using configuration in file:/opt/hive/conf/hive-log4j2.properties Async: true
Hive Session ID = b0df1385-6a1c-433d-bd14-130e0bb8fc49
OK
year=2008/month=1
year=2008/month=2
year=2008/month=3
Time taken: 1.171 seconds, Fetched: 3 row(s)
```

```bash
docker exec -ti hive-metastore hive -e 'MSCK REPAIR TABLE flight_db.flights_t;'
```

```bash
guido.schmutz@AMAXDKFVW0HYY ~/w/platys-hms> docker exec -ti hive-metastore hive -e 'MSCK REPAIR TABLE flight_db.flights_t;'

SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/opt/hive/lib/log4j-slf4j-impl-2.17.1.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/opt/hadoop/share/hadoop/common/lib/slf4j-log4j12-1.7.25.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]
Hive Session ID = 60320fed-663e-4cef-9843-bde297948e7d

Logging initialized using configuration in file:/opt/hive/conf/hive-log4j2.properties Async: true
Hive Session ID = 0e40d023-e51a-4772-9927-a1a33bafe5bf
OK
Partitions missing from filesystem:	flights_t:year=2008/month=3
Time taken: 3.038 seconds, Fetched: 1 row(s)
```

* if on **Hive Metastore 4.0.1**

```bash
docker exec -ti hive-server beeline -u jdbc:hive2://hive-server:10000 -e "SHOW PARTITIONS flight_db.flights_t;"
```

```bash
INFO  : Compiling command(queryId=hive_20250703090923_038c0de7-c392-4a44-9c6b-4bb591c6aa35): SHOW PARTITIONS flight_db.flights_t
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Semantic Analysis Completed (retrial = false)
INFO  : Returning Hive schema: Schema(fieldSchemas:[FieldSchema(name:partition, type:string, comment:from deserializer)], properties:null)
INFO  : Completed compiling command(queryId=hive_20250703090923_038c0de7-c392-4a44-9c6b-4bb591c6aa35); Time taken: 0.343 seconds
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Executing command(queryId=hive_20250703090923_038c0de7-c392-4a44-9c6b-4bb591c6aa35): SHOW PARTITIONS flight_db.flights_t
INFO  : Starting task [Stage-0:DDL] in serial mode
INFO  : Completed executing command(queryId=hive_20250703090923_038c0de7-c392-4a44-9c6b-4bb591c6aa35); Time taken: 0.112 seconds
INFO  : OK
INFO  : Concurrency mode is disabled, not creating a lock manager
+--------------------+
|     partition      |
+--------------------+
| year=2008/month=1  |
| year=2008/month=2  |
| year=2008/month=3  |
+--------------------+
```

if we use Trino to sync partition metadata with the `FULL` option, the no-existing partitions are removed

```bash
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "call minio.system.sync_partition_metadata('flight_db', 'flights_t', 'FULL')"
```


```bash
docker exec -ti hive-server beeline -u jdbc:hive2://hive-server:10000 -e "SHOW PARTITIONS flight_db.flights_t;"
```

```bash
INFO  : Compiling command(queryId=hive_20250703091030_d171fc32-d31b-43fd-97e9-14481eaa5015): SHOW PARTITIONS flight_db.flights_t
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Semantic Analysis Completed (retrial = false)
INFO  : Returning Hive schema: Schema(fieldSchemas:[FieldSchema(name:partition, type:string, comment:from deserializer)], properties:null)
INFO  : Completed compiling command(queryId=hive_20250703091030_d171fc32-d31b-43fd-97e9-14481eaa5015); Time taken: 0.144 seconds
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Executing command(queryId=hive_20250703091030_d171fc32-d31b-43fd-97e9-14481eaa5015): SHOW PARTITIONS flight_db.flights_t
INFO  : Starting task [Stage-0:DDL] in serial mode
INFO  : Completed executing command(queryId=hive_20250703091030_d171fc32-d31b-43fd-97e9-14481eaa5015); Time taken: 0.066 seconds
INFO  : OK
INFO  : Concurrency mode is disabled, not creating a lock manager
+--------------------+
|     partition      |
+--------------------+
| year=2008/month=1  |
| year=2008/month=2  |
+--------------------+
2 rows selected (0.376 seconds)
```


**Check with Trino**

```
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select count(*) from minio.flight_db.airport_t"
```

returns `1240`

```sql
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select count(*) from minio.flight_db.flights_t" 
```

returns `1175001`


## Performance Testing "Repair"

 * `hms_loadtest_base.py` - base functions for all other scripts
 * `hms_loadtest_create_tabeles.py` - create the configured number of `flights_n_t` tables
 * `hms_loadtest_upload_data.py` - uploads a configurable number of partitions into the `flights_n_t` tables
 * `hms_loadtest_remove_partitions.py`
 * `hms_loadtest_repair.py`

### `30'000` objects

```bash
cd $PYTEST_HOME
pytest src/hms_backup_restore_loadtest.py --verbose
```

```bash
docker exec -ti hive-server beeline -u jdbc:hive2://hive-server:10000 -e "SHOW PARTITIONS flight_db.flights_t;"
```

```bash
time docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "call minio.system.sync_partition_metadata('flight_db', 'flights_t', 'FULL')"
```

```
guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/platys-hms (main)> time docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "call minio.system.sync_partition_metadata('flight_db', 'flights_t', 'FULL')"
CALL

________________________________________________________
Executed in   93.17 secs      fish           external
   usr time   10.46 millis    0.19 millis   10.27 millis
   sys time   10.11 millis    1.08 millis    9.03 millis
```

### `60'000` objects

```bash
time docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "call minio.system.sync_partition_metadata('flight_db', 'flights_t', 'FULL')"
```

```bash
--execute "call minio.system.sync_partition_metadata('flight_db', 'flights_t', 'FULL')"
CALL

________________________________________________________
Executed in  230.24 secs      fish           external
   usr time   15.42 millis    0.42 millis   15.00 millis
   sys time   22.62 millis    3.20 millis   19.42 millis
```

----
Remove the last 10 partitions in Mino assuming that we have restored a newer Hive Metastore DB snapshot.

Time the "repair" operation

```bash
time docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "call minio.system.sync_partition_metadata('flight_db', 'flights_t', 'FULL')"
```


### `1000` tables with `12` partitions with `5` objects each - `60'000` objects

#### How long does it take to repair all of them if the table is "just empty"?

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-backup-restore (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in  278.23 secs    fish           external
   usr time    6.81 secs    0.39 millis    6.81 secs
   sys time    1.54 secs    3.09 millis    1.53 secs
```


#### How long does it take to repair if for all `1000` tables `3` partitions each are missing?

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-backup-restore (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   79.85 secs    fish           external
   usr time    7.23 secs    0.19 millis    7.23 secs
   sys time    1.82 secs    1.38 millis    1.82 secs
```

### `1000` tables with `24` partitions with `5` objects each - `120'000` objects


#### How long does it take to repair all of them if the table is "just empty"?

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-backup-restore (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in  555.77 secs    fish           external
   usr time    6.79 secs    0.16 millis    6.79 secs
   sys time    1.63 secs    1.36 millis    1.63 secs
```


#### How long does it take to repair if for all `1000` tables `3` partitions each are missing?

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-backup-restore (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   49.08 secs    fish           external
   usr time    6.02 secs    0.21 millis    6.02 secs
   sys time    1.17 secs    1.48 millis    1.16 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-backup-restore (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   60.60 secs    fish           external
   usr time    6.07 secs    0.18 millis    6.07 secs
   sys time    1.24 secs    1.40 millis    1.23 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-backup-restore (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   53.41 secs    fish           external
   usr time    6.51 secs    0.18 millis    6.51 secs
   sys time    1.38 secs    1.29 millis    1.38 secs
```


#### How long does it take to repair it for all `1000` tables if `3` partitions are additionally available?

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-backup-restore (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   52.59 secs    fish           external
   usr time    6.43 secs    0.18 millis    6.43 secs
   sys time    1.54 secs    1.30 millis    1.53 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/platys-hms (main) [0|1]> cd $PYTEST_HOME
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-backup-restore (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   64.24 secs    fish           external
   usr time    7.17 secs    0.19 millis    7.17 secs
   sys time    1.79 secs    1.48 millis    1.79 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-backup-restore (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   65.14 secs    fish           external
   usr time    6.53 secs    0.17 millis    6.53 secs
   sys time    1.74 secs    1.20 millis    1.74 secs
```

