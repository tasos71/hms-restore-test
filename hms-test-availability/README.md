# Test Availability of Hive Metastore Service

A suite of `pytest` to test if Hive Metastore Service (HMS) is up and running and can be used over the Thrift API.

Both list operations (for catalogs, databases and tables) are used as well as a create and drop of a table is tested, so we are sure that the Hive Metastore is up and running for read as well as write operations.

## Prepare environment

```bash
python3.11 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

## Generate Thrift objects (optional)

Perform this step, if you don't want to use the generated version of the code available in `gen-py` folder.

```bash
thrift --gen py thrift_defs/share/fb303/if/fb303.thrift
thrift --gen py thrift_defs/hive_metastore.thrift
```

## Run the tests

Set environment variables

```bash
export HMS_HOST=localhost
export HMS_PORT=9083
export HMS_TEMP_TABLE_NAME=hms_test_availability_t
export HMS_TEMP_TABLE_DBNAME=default
export HMS_TEMP_TABLE_LOCATION=s3a://admin-bucket/hms_test_availability_t
```

### Run it in verbose mode

```bash
pytest hms-test-availability.py --verbose
```

### Run it with html result

```bash
pytest hms-test-availability.py --html ./report/db-compare.html
```

### Run it with junit result

```bash
pytest hms-test-availability.py --junitxml=./junitresult/db-compare.xml
```

format it to an HTML page
```bash
docker run --rm -v ./junitresult:/results maxmiorim/junit-viewer > ./report/junit-hms-availability.html
```
