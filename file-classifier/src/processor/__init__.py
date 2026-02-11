import os
from .utils import convert_to_new_format, extract_image
from .file_reader import read_docx, read_txt, read_xlsx, read_csv, read_pdf

def read_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    file_path = convert_to_new_format(file_path)

    if ext in [".doc", ".docx"]:
        pages = read_docx(file_path)
    elif ext == ".txt":
        pages = read_txt(file_path)
    elif ext in [".xls", ".xlsx"]:
        pages = read_xlsx(file_path)
    elif ext == ".csv":
        pages = read_csv(file_path)
    elif ext == ".pdf":
        pages = read_pdf(file_path)
    else:
        pages = []
    
    readable = len(pages[0]) + len(pages[1]) > 0
    images = extract_image(file_path, readable)
    return pages[0], pages[1], images