import time
import cv2
from .utils import detect_tables, process_table, build_ocr_index, get_boxed_image
from .predictor import vietocr_predictor
from config import get_logger
logger = get_logger(__name__)


viet_ocr = vietocr_predictor()

### OCR ###

def predict_boxes(img, boxes):
    crop_images = []
    img_metadata = []
    for box in boxes:
        crop_img, meta = get_boxed_image(img, box)
        crop_images.append(crop_img)
        img_metadata.append(meta)

    texts = viet_ocr.predict_batch_bucket(crop_images)

    return (texts, img_metadata)


### FUNCTIONS ###

def process_image(img_path, boxes):
    logger.info(f"Processing image: {img_path}...")
    start = time.time()
    img = cv2.imread(img_path)
    tables = []

    text_lines, meta = predict_boxes(img, boxes)
    ocr_index = build_ocr_index(text_lines, meta)
    table_boxes = detect_tables(img)

    if table_boxes:
        for t_id, t_box in enumerate(table_boxes):
            table_data = process_table(img, t_box, ocr_index)
            tables.append({"table": t_id, "cells": table_data})
        
        rem_texts = [t["text"] for t in ocr_index if not t["used"]]
        texts = [{"text": rem_texts}] if rem_texts else []
    else:
        texts = [{"text": text_lines}]

    logger.info(f"Total processing time for image {img_path} (s): {time.time()-start:.2f}")
    return texts, tables
