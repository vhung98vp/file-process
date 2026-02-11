import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', 
    handlers=[logging.StreamHandler(sys.stdout)]
)

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger

APP = {
    'large_batch_size': int(os.environ.get('APP_LARGE_BATCH_SIZE', 32)),
    'small_batch_size': int(os.environ.get('APP_SMALL_BATCH_SIZE', 64)),
}

KAFKA = {
    'brokers': os.environ.get('KAFKA_BOOTSTRAP_SERVER'),
    'consumer_group': os.environ.get('KAFKA_CONSUMER_GROUP', 'default'),
    'consumer_timeout': float(os.environ.get('KAFKA_CONSUMER_TIMEOUT', 1)),
    'auto_offset_reset': os.environ.get('KAFKA_AUTO_OFFSET_RESET', 'earliest'),
    'input_textbox_topic': os.environ.get('KAFKA_INPUT_TEXTBOX_TOPIC'),
    'result_text_topic': os.environ.get('KAFKA_RESULT_TEXT_TOPIC'),
    'result_table_topic': os.environ.get('KAFKA_RESULT_TABLE_TOPIC'),
    'error_topic': os.environ.get('KAFKA_ERROR_TOPIC'),
}

KAFKA_CONSUMER_CONFIG = {
    'bootstrap.servers': KAFKA['brokers'],
    'group.id': KAFKA['consumer_group'],
    'auto.offset.reset': KAFKA['auto_offset_reset']
}

KAFKA_PRODUCER_CONFIG = {
    'bootstrap.servers': KAFKA['brokers']
}
