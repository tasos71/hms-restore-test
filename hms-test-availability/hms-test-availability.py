import sys
import os
from thrift.transport import TSocket, TTransport
from thrift.protocol import TBinaryProtocol

sys.path.append('gen-py')

from hive_metastore import ThriftHiveMetastore

# Read connection details from environment variables
HMS_HOST = os.getenv('HMS_HOST', 'localhost')
HMS_PORT = os.getenv('HMS_PORT', '9083')

def getClient():
    # Connect
    transport = TSocket.TSocket(HMS_HOST, HMS_PORT)  # change to your metastore host
    transport = TTransport.TBufferedTransport(transport)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = ThriftHiveMetastore.Client(protocol)
    transport.open()
    return client, transport


def test_get_catalogs():
    client, transport = getClient()
    
    catalogs = client.get_catalogs()
    
    assert len(catalogs.names), f"No catalogs have been found, should be more than 0"

    # Close connection
    transport.close()

def test_get_databases():
    client, transport = getClient()
    
    databases = client.get_all_databases()
    
    assert len(databases), f"No databases have been found, should be more than 0"

    # Close connection
    transport.close()


def test_get_tables():
    client, transport = getClient()

    databases = client.get_all_databases()

    for db in databases:
        if db == 'default':
            continue
        tables = client.get_all_tables(db)
        assert len(tables), f"No tables have been found in database '{db}', should be more than 0"

    # Close connection
    transport.close()


def test_create_table():
    client, transport = getClient()

    database = 'default'
    table_name = 'test_table'
    fields = [
        ThriftHiveMetastore.FieldSchema(name='id', type='int', comment='ID'),
        ThriftHiveMetastore.FieldSchema(name='name', type='string', comment='Name'),
    ]
    table_def = ThriftHiveMetastore.Table(
        tableName=table_name,
        dbName=database,
        tableType='EXTERNAL_TABLE',

        sd=ThriftHiveMetastore.StorageDescriptor(
            cols=fields,
            location='s3a://flight-bucket/test',
            inputFormat='org.apache.hadoop.mapred.TextInputFormat',
            outputFormat='org.apache.hadoop.mapred.TextInputFormat',
            serdeInfo=ThriftHiveMetastore.SerDeInfo(
                name='test_serde',
                serializationLib='org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe',
                parameters={}
            )
        )
    )
    
    client.create_table(table_def)

    # Close connection
    transport.close()    


def test_drop_table():
    client, transport = getClient()

    database = 'default'

    table_name = 'test_table'
    client.drop_table(database, table_name, True)

    # Close connection
    transport.close()        