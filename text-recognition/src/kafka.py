import json
import time
import uuid
import os
from confluent_kafka import Consumer, Producer
from config import get_logger, KAFKA, KAFKA_CONSUMER_CONFIG, KAFKA_PRODUCER_CONFIG
from processor import process_image
logger = get_logger(__name__)


# Kafka setup
producer = Producer(KAFKA_PRODUCER_CONFIG)
consumer = Consumer(KAFKA_CONSUMER_CONFIG)
consumer.subscribe([KAFKA['input_image_topic']])


def process_message(msg_key, msg):
    start_time = time.time()
    try:
        data = json.loads(msg)
        file_id = data.get("file_id")
        path = data.get("path")
        img_path = data.get("image")
        boxes = data.get("boxes")

        texts, tables = process_image(img_path, boxes)
        img_name = os.path.basename(img_path)
        # Send text to kafka
        if texts:
            send_output_to_kafka({"file_id": file_id, "path": path, "image": img_name, "texts": texts}, KAFKA["result_text_topic"]) 

        # Send tables to kafka
        if tables:
            send_output_to_kafka({"file_id": file_id, "path": path, "image": img_name, "tables": tables}, KAFKA["result_table_topic"]) 

    except Exception as e:
        logger.exception(f"Error while processing message {msg_key}:{msg}: {e}")
        log_error_to_kafka(msg_key, { 
            "error": str(e), 
            "message": msg 
        })
        raise e
    finally:
        logger.info(f"Processed message {msg_key} in {time.time() - start_time:.4f} seconds")


def start_kafka_consumer():
    processed_count = 0
    error_count = 0
    last_wait_time = 0
    try:
        while True:
            msg = consumer.poll(KAFKA['consumer_timeout'])
            if msg is None or msg.error():
                if msg is None:
                    cur_time = time.time()
                    if cur_time - last_wait_time > 60:
                        logger.info("Waiting for messages...")
                        last_wait_time = cur_time
                else:
                    logger.error(f"Message error: {msg.error()}")
                continue
            try:
                message = msg.value().decode("utf-8")
                message_key = msg.key().decode("utf-8") if msg.key() else None
                if not message_key:
                    logger.warning(f"Received message without key: {message}")
                process_message(message_key, message)
                processed_count += 1
            except Exception as e:
                error_count += 1
    except Exception as e:
        logger.exception(f"Consumer process terminated: {e}")
    finally:
        consumer.close()
        producer.flush()
        logger.info(f"Processed {processed_count} messages with {error_count} errors.")


def send_output_to_kafka(result, topic):
    try:
        producer.produce(topic, key=str(uuid.uuid4()), value=json.dumps(result, ensure_ascii=False))
        producer.poll(0)
    except Exception as e:
        logger.exception(f"Error sending result to output topic: {e}")


def log_error_to_kafka(msg_key, error_info: dict):
    try:
        producer.produce(KAFKA['error_topic'], key=msg_key, value=json.dumps(error_info, ensure_ascii=False))
        producer.flush()
    except Exception as e:
        logger.exception(f"Error sending to error topic: {e}")
