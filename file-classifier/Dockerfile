FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libreoffice \
    fonts-dejavu \
    libxext6 libxrender1 libxinerama1 libfreetype6 \
    ghostscript \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY /src /app
WORKDIR /app

CMD ["python", "app.py"]