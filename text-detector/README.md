# Text-detector service
- This service helps to extract all textbox in image

## Process
- Receive image from kafka (Path in Shared PV)
- Process GPU (in batch consider later)
- Detect all textbox in image
- Send textbox's metadata (coordinate) to recognition topic
