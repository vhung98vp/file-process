FROM paddlepaddle/paddle:2.6.2-gpu-cuda11.7-cudnn8.4-trt8.4

ENV DEBIAN_FRONTEND=noninteractive 


COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


COPY /models /app/models/
COPY /src /app
WORKDIR /app

ENTRYPOINT ["python", "app.py"]