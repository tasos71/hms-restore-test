import boto3
import os
import hashlib
from datetime import datetime
from collections import defaultdict
from datetime import datetime, timezone
from urllib.parse import urlparse

# Connect to MinIO or AWS S3
# Read endpoint URL from environment variable, default to localhost MinIO
endpoint_url = os.getenv('S3_ENDPOINT_URL', 'http://localhost:9000')
bucket = os.getenv('S3_BUCKET', 'flight-bucket')
prefix = os.getenv('S3_PREFIX', 'refined')  # optionally, specify a prefix

baseline_bucket = os.getenv('S3_BASELINE_BUCKET', 'admin-bucket')
baseline_object_name = os.getenv('S3_BASELINE_OBJECT_NAME', 'baseline_s3.csv')

# Create S3 client configuration
s3_config = {"service_name": "s3"}
if endpoint_url:
    s3_config["endpoint_url"] = endpoint_url

s3 = boto3.client(**s3_config)

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
        "fingerprint": fingerprint,
        "timestamp": int(latest_ts.timestamp())
    }

with open(baseline_object_name, "w") as f:
    # Print CSV header
    print("s3_location,partition_count,fingerprint,timestamp", file=f)
                
    # Iterate through Hive tables
    for table_num in range(0, 10):
        info = get_partition_info(f"s3a://{bucket}/{prefix}/flights_{table_num}_t")
        print(f"{info['s3_location']},{info['partition_count']},{info['fingerprint']},{info['timestamp']}", file=f)

# upload the file to S3 to make it available
s3.upload_file(baseline_object_name,baseline_bucket, baseline_object_name)