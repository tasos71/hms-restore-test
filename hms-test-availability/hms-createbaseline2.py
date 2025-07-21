import sys
from thrift.transport import TSocket, TTransport
from thrift.protocol import TBinaryProtocol

sys.path.append('gen-py')

from hive_metastore import ThriftHiveMetastore

# Connect
transport = TSocket.TSocket('localhost', 9083)  # change to your metastore host
transport = TTransport.TBufferedTransport(transport)
protocol = TBinaryProtocol.TBinaryProtocol(transport)
client = ThriftHiveMetastore.Client(protocol)
transport.open()

# 1. List catalogs
catalogs = client.get_catalogs()
print("Catalogs:", catalogs)

# 2. List databases in each catalog
for catalog in catalogs.names:
    databases = client.get_all_databases()
    print(f"Databases in catalog '{catalog}':", databases)

    # 3. List tables in each database
    for db in databases:
        tables = client.get_all_tables(db)
        print(f"Tables in {catalog}.{db}:", tables)
