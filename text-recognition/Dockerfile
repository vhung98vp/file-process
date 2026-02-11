FROM pytorch/pytorch1.13.1-cuda11.6-cudnn8-runtime

ENV DEBIAN_FRONTEND=noninteractive 

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY /models /app/models/
COPY /src /app
WORKDIR /app

ENTRYPOINT ["python", "app.py"]
