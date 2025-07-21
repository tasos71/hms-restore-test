# Kafkistry

Registry service for Apache Kafka which keeps track of topics, consumer-groups, acls, quotas and their configuration/state/metadata across multiple kafka-clusters.

It allows performing administrative operations such as inspecting/creating/deleting/re-configuring topics/consumer-groups.

It also provides various analytical tools such as: SQL querying metadata; viewing topic records; analyzing json record structures; re-balancing cluster tools; etc.

**[Website](https://github.com/infobip/kafkistry)** | **[Documentation](https://github.com/infobip/kafkistry/blob/master/DOCUMENTATION)** | **[GitHub](https://github.com/infobip/kafkistry/tree/master)**

## How to enable?

```
platys init --enable-services KAFKISTRY
platys gen
```

## How to use?

<<<<<<< Updated upstream
Navigate to <http://192.168.1.112:28303> to show the Kafkistry UI.
=======
Navigate to <http://10.156.72.251:28303> to show the Kafkistry UI.
>>>>>>> Stashed changes

Login as the **Admin User**: User `admin` and Password `abc123!`.
