import json
import time
import uuid
from confluent_kafka import Consumer, Producer
from config import get_logger, KAFKA, KAFKA_CONSUMER_CONFIG, KAFKA_PRODUCER_CONFIG, APP
from processor.file_reader import read_file
from processor.utils import build_doc_uid
from s3 import RClient
logger = get_logger(__name__)


# Kafka setup
producer = Producer(KAFKA_PRODUCER_CONFIG)
consumer = Consumer(KAFKA_CONSUMER_CONFIG)
consumer.subscribe([KAFKA['input_file_topic']])


def process_s3_file(key):
    try:
        local_file_path = RClient.download_file(key)
        file_id = build_doc_uid(key)
        texts, tables, images = read_file(local_file_path)

        # Send text to kafka
        send_output_to_kafka({"file_id": file_id, "path": key, "texts": texts}, KAFKA["result_text_topic"])

        # Send content to kafka
        send_output_to_kafka({"file_id": file_id, "path": key, "tables": tables}, KAFKA["result_table_topic"])

        # Send image local path to kafka
        send_output_to_kafka({"file_id": file_id, "path": key, "images": images}, KAFKA["input_image_topic"])

        return file_id
    except Exception as e:
        logger.error(f"Got error while processing file {key}: {e}")
        return None


def process_message(msg_key, msg):
    start_time = time.time()
    try:
        data = json.loads(msg)
        folder = data.get("folder")
        file_key = data.get("file")
        detect_type = data.get("type", '0')
        if detect_type not in ['0', '1', '2', '3']:
            raise ValueError(f"Invalid input type: {data}")
        if folder:
            processed = []
            file_keys = RClient.list_files(folder)
            for file_key in file_keys:
                file_id = process_s3_file(file_key, int(detect_type))
                if file_id:
                    processed.append(file_id)
            if processed:
                send_output_to_kafka({"folder": folder, "processed_files": processed}, KAFKA["complete_topic"])
                logger.info(f"Processed folder: {folder}.")
        elif file_key:
            process_s3_file(file_key, int(detect_type))
            logger.info(f"Processed file: {file_key}.")
        else:
            raise ValueError(f"Invalid input file/folder: {data}")

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


def send_output_to_kafka(result, topic=KAFKA['output_topic']):
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
