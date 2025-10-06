# Setup HMS with Data

The platform with a set of tables in HMS can be setup following these steps.

## Preparation of environment

```bash
cd ../platys-hms

export DATAPLATFORM_HOME=${PWD}

docker compose down
docker volume prune -f

docker compose up -d
```

Set environment variables

````bash
export AWS_ACCESS_KEY=admin
export AWS_SECRET_ACCESS_KEY=abc123abc123
```

## Create tables

Available Scripts

 * `hms_loadtest_base.py` - base functions for all other scripts
 * `hms_loadtest_create_tabeles.py` - creates the configured number of `flights_n_t` tables
 * `hms_loadtest_upload_data.py` - uploads a configurable number of partitions into the `flights_n_t` tables
 * `hms_loadtest_remove_objects.py` - remove a configurable number of objects from the "end" of the table
 * `hms_loadtest_remove_partitions.py` - remove a the last partition from the "end" of the table
 * `hms_loadtest_repair.py` - runs the Trino HMS repair operation for all tables

Create 12 partitioned tables

```bash
python -m src.hms_loadtest_create_tables 12
```

Add data to these tables

```bash
python -m src.hms_loadtest_upload_data 2009 10 1 true false
```

