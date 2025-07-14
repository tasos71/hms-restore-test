import thriftpy2
from thriftpy2.rpc import make_client

hms_thrift = thriftpy2.load("thrift_defs/hive_metastore.thrift", module_name="hms_thrift")

client = make_client(
    hms_thrift.ThriftHiveMetastore,
    host='localhost',
    port=9083,
    timeout=5000  # milliseconds
)

# List catalogs (Hive 4.x feature)
catalogs = client.get_catalogs()
print("Catalogs:", catalogs)

# List databases in a catalog
databases = client.get_all_databases('hive')
print("Databases:", databases)

# List tables in a database
tables = client.get_all_tables('default')
print("Tables in 'default':", tables)
