# Database comparision using pytest

## Prepare environment

```bash
python3.11 -m venv myenv
source myenv/bin/activate

pip install -r requirements.txt
```

## Run the tests

Set environment variables

```bash
export SRC_DB_USER=hive
export SRC_DB_PASSWORD=abc123!
export SRC_DB_HOST=localhost
export SRC_DB_PORT=5442
export SRC_DB_NAME=metastore_db

export TGT_DB_USER=hive
export TGT_DB_PASSWORD=abc123!
export TGT_DB_HOST=localhost
export TGT_DB_PORT=5442
export TGT_DB_NAME=metastore_db
```

### Run it in verbose mode

```bash
pytest db-compare.py --verbose
```

### Run it with html result

```bash
pytest db-compare.py --html ./report/db-compare.html
```

### Run it with junit result

```bash
pytest db-compare.py --junitxml=./junitresult/db-compare.xml
```

format it to an HTML page
```bash
docker run --rm -v ./junitresult:/results maxmiorim/junit-viewer > ./report/junit-db-compare.html
```
