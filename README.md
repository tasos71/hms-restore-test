# Test Hive Metastore Backup & Restore

## Preparation of environment

```bash
sudo rm -R backup
mkdir -p backup

docker compose down
docker volume prune -f

rm -R container-volume/minio/*
docker compose up -d

docker exec -ti minio-mc mc rb minio-1/flight-bucket --force

docker exec -ti minio-mc mc mb minio-1/flight-bucket
docker exec -ti minio-mc mc version enable minio-1/flight-bucket
```

verify that versioning works

```bash
docker exec -ti minio-mc mc version info minio-1/flight-bucket
```

Create the Kafka Audit Log topic

```bash
docker exec -ti kafka-1 kafka-topics --create --bootstrap-server kafka-1:19092 --topic minio-audit-log
```

**Create Hive Metastore Table**

```bash
docker exec -ti hive-metastore hive
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

SELECT * FROM airport_t LIMIT 5;

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

SELECT * FROM flights_t LIMIT 10;

exit;
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

**Backup Minio (no longer needed)**

```bash
cp -R container-volume/minio/ backup/1
```

## Handle period 2

```bash
touch backup/minio-savepoint-1
```

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

```sql
use flight_db;

CREATE EXTERNAL TABLE flights_per_carrier_t (
  uniquecarrier STRING,
  flight_count BIGINT
)
STORED AS PARQUET
LOCATION 's3a://flight-bucket/refined/flights-per-carrier';

INSERT INTO flights_per_carrier_t
SELECT uniquecarrier, COUNT(*) AS flight_count
FROM flight_db.flights_t
GROUP BY uniquecarrier;

exit;
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
"8","8","ALTER_TABLE","2025-06-26 09:55:54.000 UTC"
```

**Backup Minio (no longer needed)**

```bash
cp -R container-volume/minio/ backup/2
```

## Handle period 3

```bash
touch backup/minio-savepoint-2
```

**Upload `flights`**

```bash
docker exec -ti minio-mc mc cp --recursive /data-transfer/flight-data/flights-medium-parquet-partitioned/flights/year=2008/month=3 minio-1/flight-bucket/refined/flights/year=2008/
```

```bash
docker exec -ti hive-metastore hive -e 'MSCK REPAIR TABLE flight_db.flights_t;'
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
"8","8","ALTER_TABLE","2025-06-26 09:55:54.000 UTC"
"9","9","ADD_PARTITION","2025-06-26 09:57:13.000 UTC"
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

**Backup Minio (no longer needed)**

```bash
cp -R container-volume/minio/ backup/3
```

## Handle period 4

```bash
touch backup/minio-savepoint-3
```

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
"8","8","ALTER_TABLE","2025-06-26 15:23:19.000 UTC"
"9","9","ADD_PARTITION","2025-06-26 15:25:07.000 UTC"
"10","10","ADD_PARTITION","2025-06-26 15:31:19.000 UTC"
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

**Backup Minio & Hive Metastore (no longer needed)**

```bash
cp -R container-volume/minio/ backup/4
```

## Handle Period 5

```bash
touch backup/minio-savepoint-4
```

**Backup Hive Metastore (C)**

```bash
docker exec -t hive-metastore-db pg_dump -U hive -d metastore_db -F c -f /hms-D.dump
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

Calcuate of how much to rollback to

```bash
set file ./backup/minio-savepoint-2
set file_time (stat -f %m $file)
set now_time (date +%s)
set duration (math $now_time - $file_time)

echo "rollback to $duration seconds back"
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

**Check with Trino**

```
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select count(*) from minio.flight_db.airport_t"
```

returns `1240`

```sql
docker exec -ti trino-cli trino --server http://trino-1:8080  --user trino --execute "select count(*) from minio.flight_db.flights_t" 
```

returns `1175001`


