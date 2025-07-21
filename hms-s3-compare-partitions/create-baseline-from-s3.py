import boto3
from datetime import datetime
from collections import defaultdict
from datetime import datetime, timezone

# Connect to MinIO
s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="admin",
    aws_secret_access_key="abc123abc123",
)

bucket = "flight-bucket"
prefix = "refined"  # optionally, specify a base prefix

# Dictionary to track folder and earliest object timestamp
folders = defaultdict(lambda: datetime.max.replace(tzinfo=timezone.utc))

paginator = s3.get_paginator("list_objects_v2")
pages = paginator.paginate(Bucket=bucket, Prefix=prefix)


for page in pages:
    for obj in page.get("Contents", []):
        key = obj["Key"]
        last_modified = obj["LastModified"]

        if "/" in key:
            folder = key.rsplit("/", 1)[0]

            folders[folder] = min(folders[folder], last_modified)

# Display results
for folder, creation_time in folders.items():
    print(f"{folder}/ -> Created: {creation_time}")
