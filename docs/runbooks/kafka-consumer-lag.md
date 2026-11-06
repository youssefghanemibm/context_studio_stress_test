# Kafka consumer lag

1. Identify the consumer group and topic from the alert.
2. Check whether the producer published an unusual volume (bridge batches arrive once a day).
3. Scale the consumer deployment only if lag keeps growing after the batch has drained.
4. If a poison message blocks a partition, move it to the dead-letter topic and replay later.
