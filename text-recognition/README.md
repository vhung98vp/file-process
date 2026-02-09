# Text-recognition service
- This service helps to recognition all text and table in image

## Process
- Receive textbox input from kafka (Path in Shared PV)
- Crop all textbox to cv2 image type
- Process GPU in batch
- Recognize text inside all textbox
- Detect all table structure inside image. If have any table:
    + Fit text to table
    + Remove text from full-text result
- Send text and table to result topic
- Send process done flag to Redis:
    + If all process done, clean up file in Shared PV
