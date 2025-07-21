# Remora

Kafka consumer lag-checking application for monitoring, written in Scala and Akka HTTP; a wrap around the Kafka consumer group command. Integrations with Cloudwatch and Datadog. Authentication recently added 

**[Documentation](https://github.com/zalando-incubator/remora)** | **[GitHub](https://github.com/zalando-incubator/remora)**

## How to enable?

```
platys init --enable-services KAFKA,REMORA
platys gen
```

## How to use it?

Show active consumers

```bash
<<<<<<< Updated upstream
curl http://192.168.1.112:28256/consumers
=======
curl http://10.156.72.251:28256/consumers
>>>>>>> Stashed changes
```

Show specific consumer group information

```bash
<<<<<<< Updated upstream
curl http://192.168.1.112:28256/consumers/<consumer-group-id>
=======
curl http://10.156.72.251:28256/consumers/<consumer-group-id>
>>>>>>> Stashed changes
```

Show health

```bash
<<<<<<< Updated upstream
curl http://192.168.1.112:28256/health
=======
curl http://10.156.72.251:28256/health
>>>>>>> Stashed changes
```

Metrics

```bash
<<<<<<< Updated upstream
curl http://192.168.1.112:28256/metrics
=======
curl http://10.156.72.251:28256/metrics
>>>>>>> Stashed changes
```
