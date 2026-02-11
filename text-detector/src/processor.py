from paddleocr import PaddleOCR
import numpy as np
import time
import os
from config import get_logger
logger = get_logger(__name__)


paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=True, precision="fp16",
        det_model_dir="./models/det/en/en_PP-OCRv3_det_infer",
        rec_model_dir="./models/rec/en/en_PP-OCRv3_rec_infer",
        cls_model_dir="./models/cls/ch_ppocr_mobile_v2.0_cls_infer",)


def detect_boxes(img_path):
    if not os.path.exists(img_path):
        logger.error(f"Wrong image path: {img_path}")
        return []

    logger.info(f"Processing image: {img_path}...")
    start = time.time()

    ocr_result = paddle_ocr.ocr(img_path, det=True, rec=False, cls=True)
    boxes = ocr_result[0] if ocr_result else []
    if not boxes:
        return []

    boxes_sorted = sorted(
        boxes,
        key=lambda box: (
            np.mean([pt[1] for pt in box]),   # row (top → bottom)
            np.mean([pt[0] for pt in box])    # column (left → right)
        )
    )

    logger.info(f"Got {len(boxes_sorted)} boxes for {img_path} in (s): {time.time()-start:.2f}")

    return boxes_sorted