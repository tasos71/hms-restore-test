import boto3
import hashlib
from datetime import datetime
from collections import defaultdict
from datetime import datetime, timezone
from urllib.parse import urlparse

# Connect to MinIO
s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="admin",
    aws_secret_access_key="abc123abc123",
)

bucket = "flight-bucket"
prefix = "refined"  # optionally, specify a base prefix

def get_partition_info(s3a_url):
    # Convert s3a:// to s3://
    s3_url = s3a_url.replace("s3a://", "s3://")
    parsed = urlparse(s3_url)
    bucket = parsed.netloc
    prefix = parsed.path.lstrip("/")

    paginator = s3.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

    partitions = set()
    latest_ts = datetime(1970, 1, 1, tzinfo=timezone.utc)

    for page in page_iterator:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            # Detect partition-style folder structure like col=value
            parts = key[len(prefix):].strip("/").split("/")
            partition_parts = [p for p in parts if "=" in p]
            if partition_parts:
                partitions.add("/".join(partition_parts))
            if obj["LastModified"] > latest_ts:
                latest_ts = obj["LastModified"]                

    sorted_partitions = sorted(partitions)
    joined = ",".join(sorted_partitions)
    fingerprint = hashlib.sha256(joined.encode('utf-8')).hexdigest()
                      
    return {
        "s3_location": s3a_url,
        "partition_count": len(partitions),
        "timestamp": int(latest_ts.timestamp()),
        "fingerprint": fingerprint
    }


with open("baseline_s3.csv", "w") as f:
    # Print CSV header
    print("s3_location,partition_count,timestamp,fingerprint", file=f)
                
    # Iterate through Hive tables
    for table_num in range(0, 1000):
        info = get_partition_info(f"s3a://flight-bucket/refined/flights_{table_num}_t")
        print(f"{info['s3_location']},{info['partition_count']},{info['timestamp']},{info['fingerprint']}", file=f)