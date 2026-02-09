# File-classifier service
- This service helps to extract all information in readable file. It support multiple file types:
    + Document (.doc, .docx), Text (.txt)
    + Sheet (.xls, .xlsx), Table (.csv)
    + PDF (Readable with text layer)
- With image inside file, Non-readable PDF and Images, it forward all pages to image topic

## Process
- Receive input from kafka (File/Folder path)
- For each file, download it from S3 (MinIO) to Shared PV
- If file has readable text:
    + Send text and table to result topic
    + Save images inside to Shared PV, send path to image topic
- If file is non-readable:
    + If PDF, split it to pages and save to Shared PV
    + Send all image paths to image topic
