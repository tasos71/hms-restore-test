import sys
from thrift.transport import TSocket, TTransport
from thrift.protocol import TBinaryProtocol

sys.path.append('gen-py')

from hive_metastore import ThriftHiveMetastore


def getClient():
    # Connect
    transport = TSocket.TSocket('localhost', 9083)  # change to your metastore host
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