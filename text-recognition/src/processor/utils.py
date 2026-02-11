import cv2
import numpy as np


def get_boxed_image(img, box):
    pts = np.array(box).astype(int)
    x_min = np.min(pts[:, 0])
    x_max = np.max(pts[:, 0])
    y_min = np.min(pts[:, 1])
    y_max = np.max(pts[:, 1])
    crop_img = img[y_min:y_max, x_min:x_max]
    return crop_img, [y_min, y_max, x_min, x_max]


def get_lines_from_thresh(thresh, split_ratio=15):
    horizontal = thresh.copy()
    vertical = thresh.copy()

    h_size = int(horizontal.shape[1] / split_ratio)
    h_structure = cv2.getStructuringElement(cv2.MORPH_RECT, (h_size, 1))
    horizontal = cv2.erode(horizontal, h_structure)
    horizontal = cv2.dilate(horizontal, h_structure)

    v_size = int(vertical.shape[0] / split_ratio)
    v_structure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_size))
    vertical = cv2.erode(vertical, v_structure)
    vertical = cv2.dilate(vertical, v_structure)

    return horizontal, vertical


def merge_close_lines(lines, min_gap=5):
    merged = []
    current = []
    for l in lines:
        if not current:
            current.append(l)
        elif l - current[-1] <= min_gap:
            current.append(l)
        else:
            merged.append(int(np.mean(current)))
            current = [l]
    if current:
        merged.append(int(np.mean(current)))
    return merged


def get_table_grid(table_bin, split_ratio=30):
    horizontal, vertical = get_lines_from_thresh(table_bin, split_ratio)

    horizontal_sum = np.sum(horizontal, axis=1)
    vertical_sum = np.sum(vertical, axis=0)
    h_lines = [i for i in range(len(horizontal_sum)) if horizontal_sum[i] > 255*max(table_bin.shape[1] * 0.1, 200)]
    v_lines = [i for i in range(len(vertical_sum)) if vertical_sum[i] > 255*max(table_bin.shape[0] * 0.1, 200)]
    h_lines = merge_close_lines(h_lines, 20)
    v_lines = merge_close_lines(v_lines, 20)
    
    return h_lines, v_lines



def build_ocr_index(texts, boxes):
    indexed = []
    for t, (y1,y2,x1,x2) in zip(texts, boxes):
        indexed.append({
            "text": t,
            "x1": x1, "x2": x2,
            "y1": y1, "y2": y2,
            "cx": (x1+x2)/2,
            "cy": (y1+y2)/2,
            "used": False
        })
    return indexed


def map_texts_to_cells(ocr_items, cells, rows, cols, tx, ty):
    table = [[[] for _ in range(cols)] for _ in range(rows)]

    for t in ocr_items:
        if not t["used"]:
            continue
        cx = t["cx"] - tx
        cy = t["cy"] - ty

        for r,c,x1,y1,x2,y2 in cells:
            if x1 <= cx <= x2 and y1 <= cy <= y2:
                table[r][c].append((t["x1"], t["text"]))
                break

    for r in range(rows):
        for c in range(cols):
            table[r][c] = " ".join(x[1] for x in sorted(table[r][c]))

    return table


def detect_cells(table_img):
    table_gray = cv2.cvtColor(table_img, cv2.COLOR_BGR2GRAY)
    table_bin = cv2.adaptiveThreshold(
        ~table_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2
    )

    # Get horizontal and vertical lines
    h_lines, v_lines = get_table_grid(table_bin, split_ratio=30)

    cells = []  # (row_idx, col_idx)
    num_rows = len(h_lines) - 1
    num_cols = len(v_lines) - 1

    for r in range(num_rows):
        for c in range(num_cols):
            cy1, cy2 = h_lines[r], h_lines[r+1]
            cx1, cx2 = v_lines[c], v_lines[c+1]
            if cx1 == cx2 or cy1 == cy2:
                continue
            cells.append((r, c, cx1, cy1, cx2, cy2))
    return cells, num_rows, num_cols




def process_table(img, table_box, ocr_index):
    x,y,w,h = table_box
    table_img = img[y:y+h, x:x+w]

    cells, rows, cols = detect_cells(table_img)
    table_texts = []
    for t in ocr_index:
        if x <= t["cx"] <= x+w and y <= t["cy"] <= y+h:
            t["used"] = True
            table_texts.append(t)

    return map_texts_to_cells(table_texts, cells, rows, cols, x, y)


def detect_tables(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.adaptiveThreshold(
        ~blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2
    )

    horizontal, vertical = get_lines_from_thresh(thresh, split_ratio=15)
    mask = cv2.add(horizontal, vertical)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    results = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 100 and h > 100:
            results.append((x, y, w, h))
    return results