# Performance Test of Hive Metastore Repair operation

The following scenario will be tested by going through the steps documented below

![](./images/scenario.png)

## Preparation of environment

```bash
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

## Available Scripts

 * `hms_loadtest_base.py` - base functions for all other scripts
 * `hms_loadtest_create_tabeles.py` - creates the configured number of `flights_n_t` tables
 * `hms_loadtest_upload_data.py` - uploads a configurable number of partitions into the `flights_n_t` tables
 * `hms_loadtest_remove_objects.py` - remove a configurable number of objects from the "end" of the table
 * `hms_loadtest_remove_partitions.py` - remove a the last partition from the "end" of the table
 * `hms_loadtest_repair.py` - runs the Trino HMS repair operation for all tables


## Run it for `1000` tables with `12` partitions with `5` objects each - `60'000` objects

This test shows a setup with 1000 partitioned tables, each a year with 12 (monthly) partitions with 5 objects each. 

### (1) How long does it take to repair all of them if the table is "just empty"?

This test is based on the "empty" table not knowing of any of the partitions. 

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in  278.23 secs    fish           external
   usr time    6.81 secs    0.39 millis    6.81 secs
   sys time    1.54 secs    3.09 millis    1.53 secs
```

### (2) How long does it take to repair if for all `1000` tables `3` objects each in the last partition are missing?

in this test we have removed some of the objects (3 of the last partition) and are measuring a repair operation (setting HMS backwards)

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   79.85 secs    fish           external
   usr time    7.23 secs    0.19 millis    7.23 secs
   sys time    1.82 secs    1.38 millis    1.82 secs
```

### (3) How long does it take to repair if for all `1000` tables `3` objects each in the last partition are missing?

in this test we have restored the objects we have removed before (3 of the last partition) and are measuring a repair operation (setting HMS forwards)

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   77.78 secs    fish           external
   usr time    7.86 secs    0.23 millis    7.85 secs
   sys time    2.11 secs    1.97 millis    2.11 secs
```

### (4) How long does it take to repair if for all `1000` tables `1` partition each are missing?

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   39.39 secs    fish           external
   usr time    6.18 secs    0.17 millis    6.18 secs
   sys time    1.46 secs    1.16 millis    1.46 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   41.90 secs    fish           external
   usr time    6.34 secs    0.18 millis    6.34 secs
   sys time    1.45 secs    1.42 millis    1.45 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   30.86 secs    fish           external
   usr time    6.12 secs    0.17 millis    6.12 secs
   sys time    1.17 secs    1.13 millis    1.17 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   41.29 secs    fish           external
   usr time    5.76 secs    0.32 millis    5.76 secs
   sys time    1.28 secs    2.33 millis    1.27 secs
```

### (5) How long does it take to repair if for all `1000` tables `1` partition each are missing?

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   34.93 secs    fish           external
   usr time    6.37 secs    0.20 millis    6.37 secs
   sys time    1.58 secs    1.49 millis    1.58 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   38.34 secs    fish           external
   usr time    6.31 secs    0.18 millis    6.31 secs
   sys time    1.34 secs    1.13 millis    1.34 secs
```   

```
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   46.35 secs    fish           external
   usr time    6.98 secs    0.19 millis    6.98 secs
   sys time    1.63 secs    1.56 millis    1.63 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   46.22 secs    fish           external
   usr time    5.87 secs    0.17 millis    5.87 secs
   sys time    1.40 secs    1.33 millis    1.40 secs
   
```

## Run it for `1000` tables with `24` partitions with `5` objects each - `120'000` objects


### (1) How long does it take to repair all of them if the table is "just empty"?

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in  692.01 secs    fish           external
   usr time    7.36 secs    0.18 millis    7.36 secs
   sys time    1.84 secs    1.32 millis    1.84 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in  531.71 secs    fish           external
   usr time    6.60 secs    0.17 millis    6.60 secs
   sys time    1.41 secs    1.15 millis    1.41 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in  618.17 secs    fish           external
   usr time    6.93 secs    0.19 millis    6.93 secs
   sys time    1.56 secs    2.48 millis    1.56 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in  563.54 secs    fish           external
   usr time    6.46 secs    0.31 millis    6.46 secs
   sys time    1.39 secs    2.78 millis    1.39 secs
```

### (2) How long does it take to repair if for all `1000` tables `3` objects each in the last partition are missing?

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   42.61 secs    fish           external
   usr time    6.45 secs    0.30 millis    6.45 secs
   sys time    1.26 secs    2.31 millis    1.26 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   59.45 secs    fish           external
   usr time    6.89 secs    0.20 millis    6.89 secs
   sys time    1.69 secs    1.70 millis    1.69 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   47.27 secs    fish           external
   usr time    6.50 secs    0.18 millis    6.50 secs
   sys time    1.44 secs    1.32 millis    1.44 secs
```

### (3) How long does it take to repair if for all `1000` tables `3` objects each in the last partition are missing?

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   46.59 secs    fish           external
   usr time    6.35 secs    0.20 millis    6.35 secs
   sys time    1.38 secs    1.44 millis    1.38 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   62.90 secs    fish           external
   usr time    6.15 secs    0.20 millis    6.15 secs
   sys time    1.54 secs    1.28 millis    1.54 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   50.12 secs    fish           external
   usr time    6.84 secs    0.17 millis    6.84 secs
   sys time    1.65 secs    1.25 millis    1.65 secs
```

### (4) How long does it take to repair if for all `1000` tables `1` partition each are missing?

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   49.35 secs    fish           external
   usr time    6.21 secs    0.17 millis    6.21 secs
   sys time    1.17 secs    1.20 millis    1.17 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   66.95 secs    fish           external
   usr time    7.21 secs    0.33 millis    7.21 secs
   sys time    1.81 secs    2.00 millis    1.81 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   55.35 secs    fish           external
   usr time    6.36 secs    0.18 millis    6.36 secs
   sys time    1.18 secs    1.33 millis    1.18 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   50.71 secs    fish           external
   usr time    6.60 secs    0.19 millis    6.60 secs
   sys time    1.42 secs    1.32 millis    1.42 secs
```

### (5) How long does it take to repair if for all `1000` tables `1` partition each are missing?

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   57.72 secs    fish           external
   usr time    7.44 secs    0.17 millis    7.44 secs
   sys time    1.55 secs    1.24 millis    1.55 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   59.28 secs    fish           external
   usr time    6.85 secs    0.17 millis    6.85 secs
   sys time    1.54 secs    1.59 millis    1.54 secs
```

```bash
(venv) guido.schmutz@AMAXDKFVW0HYY ~/D/G/g/h/hms-s3-repair-performance-test (main)> time python -m src.hms_loadtest_repair

________________________________________________________
Executed in   49.57 secs    fish           external
   usr time    6.61 secs    0.21 millis    6.61 secs
   sys time    1.45 secs    1.60 millis    1.45 secs
```

