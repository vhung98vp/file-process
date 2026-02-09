# Object-detector service
- This service helps to extract all objects in image

## Process
- Receive image input from kafka (Path in Shared PV)
- Process GPU (in batch consider later)
- Detect all target object in image
- If have any target object in image:
    + Upload full image to S3
    + Send page & object's metadata (coordinate, type) to result topic
- Send process done flag to Redis:
    + If all process done, clean up file in Shared PV
