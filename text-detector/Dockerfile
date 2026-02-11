FROM nvidia/cuda:11.7.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive 

RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    git \
    curl \
    ccache \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

RUN add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3.10-distutils \
    python3-pip \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

RUN python3.10 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN python -m pip install paddleocr==2.8.1
RUN python -m pip install paddlepaddle-gpu==2.6.2

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


COPY /models /app/models/
COPY /src /app
WORKDIR /app

RUN mkdir -p /usr/local/lib64 && \
    if [ -f /usr/lib/x86_64-linux-gnu/libcudnn.so.8 ]; then \
        ln -sf /usr/lib/x86_64-linux-gnu/libcudnn.so.8 /usr/lib/x86_64-linux-gnu/libcudnn.so && \
        ln -sf /usr/lib/x86_64-linux-gnu/libcudnn.so.8 /usr/local/cuda/lib64/libcudnn.so; \
    fi && \
    ldconfig

ENTRYPOINT ["python", "app.py"]