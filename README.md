# File process project
This project helps to process multiple file types, extract all text and detect all target objects in images. Process type: 
- 0 - Extract all information (default)
- 1 - Extract only text 
- 2 - Extract only table
- 3 - Extract only object (in figures)

## Project structure, includes 4 main services:
- File-classifier: 
    + Doc, Sheet, Readable PDF: Extract text, table, figure (forward to image topic)
    + Send text, table to result topic
    + Non-readable PDF, Image: Split to Page-level, forward to image topic
    + All image download and save in Shared PV, only share local path to next service
- Object-detector (GPU):
    + Detect target objects in image, then if any object exists:
    + Upload full image to S3
    + Send page & object's metadata (coordinate, type) to result topic
- Text-detector (GPU):
    + Detect bounding boxes of text in image
    + Send bounding boxes to recognition topic
- Text-recognition:
    + Crop textbox, recognition all text
    + Detect table (if exist), fit text to table
    + Send text, table to result topic

### Shared service:
- Kafka: Event stream (input, process and result topic)
- S3 (MinIO): Store input files, save output files (image with target objects)
- Shared PV (PersistentVolume): Save downloaded file, shared between services, auto clean
- Redis: Save process state & clean file in Shared PV
