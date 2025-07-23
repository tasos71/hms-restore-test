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

response = client.get_catalogs()
print("Catalogs:", response.names)

# 1. List catalogs
req = ThriftHiveMetastore.GetCatalogRequest()
req.catalogName = 'hive'  # specify the catalog name if needed
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

        for table in tables:
            get_table_req = ThriftHiveMetastore.GetTableRequest()
            get_table_req.catalogName = catalog
            get_table_req.dbName = db
            get_table_req.tblName = table

            table_info = client.get_table_req(get_table_req)

            print (f"Table: {table_info.table.tableName} - {table_info.table.createTime} ")

            print(f"Table: {table}")

            # 4. Get fields of each table
            fields = client.get_fields(db, table)
            for field in fields:
                print(f"  Field: {field.name} ({field.type}) {field.comment}")

# Close connection
transport.close()
