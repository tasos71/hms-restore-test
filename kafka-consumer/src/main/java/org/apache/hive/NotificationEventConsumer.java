package org.apache.hive;


import com.fasterxml.jackson.databind.ObjectMapper;
import io.confluent.kafka.serializers.KafkaAvroSerializerConfig;
import org.apache.hadoop.hive.metastore.api.Table;
import org.apache.hadoop.hive.metastore.messaging.AlterTableMessage;
import org.apache.hadoop.hive.metastore.messaging.CreateTableMessage;
import org.apache.hadoop.hive.metastore.messaging.MessageDeserializer;
import org.apache.hadoop.hive.metastore.messaging.MessageFactory;

import org.apache.hive.hcatalog.metastore.KafkaNotificationEvent;
import org.apache.kafka.clients.consumer.*;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.consumer.ConsumerConfig;

import io.confluent.kafka.serializers.KafkaAvroDeserializer;
import io.confluent.kafka.serializers.KafkaAvroDeserializerConfig;
import org.apache.thrift.TSerializer;
import org.apache.thrift.protocol.TJSONProtocol;

import java.lang.reflect.InvocationTargetException;
import java.time.Duration;
import java.util.Collections;
import java.util.Properties;

public class NotificationEventConsumer {

  private final static String TOPIC = "hms.notification.v1";
  private final static String BOOTSTRAP_SERVERS =
          "localhost:9092, localhost:9093, localhost:9094";
  private final static String SCHEMA_REGISTRY_URL = "http://localhost:8081";

  private static Consumer<Long, KafkaNotificationEvent> createConsumer() {
    Properties props = new Properties();
    props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP_SERVERS);
    props.put(ConsumerConfig.GROUP_ID_CONFIG, "kafka-notification-cg8");
    props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");

    props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, KafkaAvroDeserializer.class.getName());
    props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, KafkaAvroDeserializer.class.getName());
    props.put(KafkaAvroDeserializerConfig.SPECIFIC_AVRO_READER_CONFIG, "true");
    props.put(KafkaAvroDeserializerConfig.SCHEMA_REGISTRY_URL_CONFIG, SCHEMA_REGISTRY_URL);   // use constant for "schema.registry.url"

    return new KafkaConsumer<>(props);
  }

  public static void main(String[] args) throws InvocationTargetException, IllegalAccessException {
        // This is a placeholder for the main method.
        // You can implement the logic to consume notification events here.
        System.out.println("NotificationEventConsumer is running...");

      MessageDeserializer deserializer = MessageFactory.getInstance("gzip").getDeserializer();

      Consumer<Long, KafkaNotificationEvent> consumer = createConsumer();

        try {
          consumer.subscribe(Collections.singletonList(TOPIC));

          while (true) {
              ConsumerRecords<Long, KafkaNotificationEvent> records = consumer.poll(Duration.ofMillis(100));
              for (ConsumerRecord<Long, KafkaNotificationEvent> record : records) {
                  System.out.printf("Consumed record: key = %s, value = %s, offset = %d%n",
                          record.key(), record.value(), record.offset());
                  if (record.value().getEventType().toString().equals("CREATE_TABLE")) {
                      System.out.println("Found CREATE TABLE");
                      CreateTableMessage createMessage = deserializer.getCreateTableMessage(record.value().getMessage().toString());
                      Table table = createMessage.getTableObj();

                      ObjectMapper mapper = new ObjectMapper();
                      String json2 = mapper.writeValueAsString(table);
                      System.out.println(json2);
                  } else if (record.value().getEventType().toString().equals("ALTER_TABLE")) {
                      AlterTableMessage alterTableMessage = deserializer.getAlterTableMessage(record.value().getMessage().toString());
                      Table tableBefore = alterTableMessage.getTableObjBefore();
                      Table tableAfter = alterTableMessage.getTableObjAfter();
                  }
              }
          }
        } catch (Exception e) {
          System.err.println("Error while consuming messages: " + e.getMessage());
          e.printStackTrace();
        } finally {
          consumer.close();
          System.out.println("Kafka consumer closed.");
        }
    
    }

}
