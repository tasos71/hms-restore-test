# Database comparision using pytest

## Prepare environment

```bash
python3.11 -m venv myenv
source venv/bin/activate

pip install -r requirements.txt
```

```bash
docker exec -ti kafka-1 kafka-topics --bootstrap-servers kafka-1:19092 --create --topic hms.table.metric.events.v1 --replication-factor 3 --partitions 3
```

## Run the tests

Set environment variables

```bash

```

### Run it in verbose mode

```bash
pytest db-compare.py --verbose
```

