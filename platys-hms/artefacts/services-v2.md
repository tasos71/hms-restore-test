# platys-platform - List of Services

| Service | Links | External<br>Port | Internal<br>Port | Description
|--------------|------|------|------|------------
|[adminio-api](./documentation/services/adminio )|[Rest API](http://10.158.124.14:28191)|28191<br>|8080<br>|MinIO Admin UI
|[adminio-ui](./documentation/services/adminio )|[Web UI](http://10.158.124.14:28190)|28190<br>|80<br>|MinIO Admin UI
|[akhq](./documentation/services/akhq )|[Web UI](http://10.158.124.14:28107) - [Rest API](http://10.158.124.14:28107/api)|28107<br>28320<br>|8080<br>28081<br>|Kafka GUI
|[hive-metastore](./documentation/services/hive-metastore )||9083<br>|9083<br>|Hive Metastore
|[hive-metastore-db](./documentation/services/hive-metastore )||5442<br>|5432<br>|Hive Metastore DB
|[kafka-1](./documentation/services/kafka )||9092<br>19092<br>29092<br>39092<br>9992<br>1234<br>|9092<br>19092<br>29092<br>39092<br>9992<br>1234<br>|Kafka Broker 1
|[kafka-2](./documentation/services/kafka )||9093<br>19093<br>29093<br>39093<br>9993<br>1235<br>|9093<br>19093<br>29093<br>39093<br>9993<br>1234<br>|Kafka Broker 2
|[kafka-3](./documentation/services/kafka )||9094<br>19094<br>29094<br>39094<br>9994<br>1236<br>|9094<br>19094<br>29094<br>39094<br>9994<br>1234<br>|Kafka Broker 3
|[markdown-viewer](./documentation/services/markdown-viewer )|[Web UI](http://10.158.124.14:80)|80<br>|3000<br>|Platys Platform homepage viewer
|[minio-1](./documentation/services/minio )|[Web UI](http://10.158.124.14:9010)|9000<br>9010<br>|9000<br>9010<br>|Software-defined Object Storage
|[minio-mc](./documentation/services/minio )||||MinIO Console
|[spark-master](./documentation/services/spark )|[Web UI](http://10.158.124.14:28304)|28304<br>6066<br>7077<br>4040-4044<br>|28304<br>6066<br>7077<br>4040-4044<br>|Spark Master Node
|[spark-worker-1](./documentation/services/spark )||28111<br>|28111<br>|Spark Worker Node
|[trino-1](./documentation/services/trino )|[Web UI](http://10.158.124.14:28082/ui/preview)|28082<br>28087<br>|8080<br>8443<br>|SQL Virtualization Engine
|[trino-cli](./documentation/services/trino )||||Trino CLI
|[zeppelin](./documentation/services/zeppelin )|[Web UI](http://10.158.124.14:28080)|28080<br>6060<br>5050<br>4050-4054<br>|8080<br>6060<br>5050<br>4050-4054<br>|Data Science Notebook|

**Note:** init container ("init: true") are not shown