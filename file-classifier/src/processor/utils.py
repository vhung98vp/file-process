import uuid
import os
import re
import zipfile
import fitz
import imagesize
import io
import subprocess
from config import get_logger, APP
logger = get_logger(__name__)


def build_doc_uid(s3_key, entity_type=APP['doc_entity_type'], namespace=APP['namespace_uuid']):
    return str(uuid.uuid5(namespace, f"{entity_type}:{s3_key}"))


def convert_to_new_format(file_path):
    """Convert .doc -> .docx and .xls -> .xlsx using LibreOffice."""
    ext = os.path.splitext(file_path)[1].lower()
    output_dir = os.path.dirname(file_path)
    if ext in [".doc", ".xls"]:
        logger.info(f"Converting {file_path} ...")
        subprocess.run([
            "libreoffice", "--headless", "--convert-to",
            "docx" if ext == ".doc" else "xlsx",
            file_path, "--outdir", output_dir
        ], check=True)
        return file_path + "x"
    return file_path


def is_copyable_pdf_page(page, threshold=0.8):
    try:
        text = page.get_text()
        if not text.strip():
            return False
        
        valid_chars = re.findall(r'[\w\s\.,;:\-\(\)]', text)
        ratio = len(valid_chars) / len(text)
        logger.info(f"Text detected. Valid character ratio: {ratio:.2f}")
        return ratio >= threshold
    except Exception:
        return False
    

def process_copyable_pdf_page(page, page_idx):
    tables = []
    texts = []
    page_lines = page.get_text("text").splitlines()
    text_lines = [line for line in page_lines if line.strip()]
            
    all_tables = page.find_tables()
    if all_tables.tables:
        for table_idx, table in enumerate(all_tables):
            cells = [[text if text else "" for text in row] for row in table.extract()]
            tables.append({"page": page_idx, "table": table_idx, "cells": cells})
            page.add_redact_annot(table.bbox)
        page.apply_redactions()
        rem_lines = page.get_text("text").splitlines()
        rem_texts = [line for line in rem_lines if line.strip()]
        texts = [{"page": page_idx, "text": rem_texts}] if rem_texts else []
    else:
        texts = [{"page": page_idx, "text": text_lines}] if text_lines else []
    
    return texts, tables


def is_valid_image(data):
    w, h = imagesize.get(io.BytesIO(data))
    return min(w, h) > APP["min_img_size"]


def write_bytes(data, out_dir, file_name):
    if is_valid_image(data):
        out_path = os.path.join(out_dir, file_name)
        with open(out_path, "wb") as f:
            f.write(data)


def get_full_path_dir(dir):
    paths = os.listdir(dir)
    if not paths:
        os.rmdir(dir)
    return [os.path.join(dir, path) for path in paths]


def extract_image(path, readable_content=True):
    ext = os.path.splitext(path)[1].lower()
    if ext in [".jpg", ".jpeg", ".jp2", ".png", ".bmp", ".webp"]:
        return [path]
    
    if ext not in [".docx", ".xlsx", ".pdf"]:
        return []
    
    out_dir = f"{path}_imgs"
    os.makedirs(out_dir, exist_ok=True)
    
    if ext in [".docx", ".xlsx"]:
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if name.startswith("word/media/") or name.startswith("xl/media/"):
                    data = z.read(name)
                    write_bytes(data, out_dir, os.path.basename(name))

    else: # ext == "pdf"
        if readable_content:
            with fitz.open(path) as pages:
                for page_idx, page in enumerate(pages):
                    images = page.get_images(full=True)
                    for img_idx, img_info in enumerate(images):
                        img_base = pages.extract_image(img_info[0])
                        data = img_base["image"]
                        ext = img_base["ext"]
                        write_bytes(data, out_dir, f"page{page_idx}_img{img_idx}.{ext}")
        else:
            with fitz.open(path) as pages:
                for page_idx, page in enumerate(pages):
                    page_path = os.path.join(out_dir, f"page_{page_idx}.png")
                    pix = page.get_pixmap(dpi=300)
                    pix.save(page_path)
    return get_full_path_dir(out_dir)