import os
import sys
import logging
import uuid
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
    'shared_path': os.environ.get('SHARED_PATH', '/tmp/appdata'),
    'doc_id_key': os.environ.get('DOC_ID_FIELD', '_fs_internal_id'),
    'doc_entity_type': os.environ.get('DOC_ENTITY_TYPE', 'fs.entity.Document'),
    'namespace_uuid': uuid.UUID(os.environ.get('NAMESPACE_UUID', "6ba7b810-9dad-11d1-80b4-00c04fd430c8")),
    'min_img_size': int(os.environ.get('MIN_IMG_SIZE', 50)),
}

KAFKA = {
    'brokers': os.environ.get('KAFKA_BOOTSTRAP_SERVER'),
    'consumer_group': os.environ.get('KAFKA_CONSUMER_GROUP', 'default'),
    'consumer_timeout': float(os.environ.get('KAFKA_CONSUMER_TIMEOUT', 1)),
    'auto_offset_reset': os.environ.get('KAFKA_AUTO_OFFSET_RESET', 'earliest'),
    'input_file_topic': os.environ.get('KAFKA_INPUT_FILE_TOPIC'),
    'input_image_topic': os.environ.get('KAFKA_INPUT_IMAGE_TOPIC'),
    'result_text_topic': os.environ.get('KAFKA_RESULT_TEXT_TOPIC'),
    'result_table_topic': os.environ.get('KAFKA_RESULT_TABLE_TOPIC'),
    'error_topic': os.environ.get('KAFKA_ERROR_TOPIC'),
    'complete_topic': os.environ.get('KAFKA_COMPLETE_TOPIC'),
}

KAFKA_CONSUMER_CONFIG = {
    'bootstrap.servers': KAFKA['brokers'],
    'group.id': KAFKA['consumer_group'],
    'auto.offset.reset': KAFKA['auto_offset_reset']
}

KAFKA_PRODUCER_CONFIG = {
    'bootstrap.servers': KAFKA['brokers']
}

S3_READ_CONFIG = {
    'endpoint': os.environ.get('S3_READ_ENDPOINT'),
    'access_key': os.environ.get('S3_READ_ACCESS_KEY_ID'),
    'secret_key': os.environ.get('S3_READ_SECRET_ACCESS_KEY'),
    'bucket_name': os.environ.get('S3_READ_BUCKET_NAME')
}
