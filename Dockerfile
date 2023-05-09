FROM arm64v8/python:3-slim

RUN apt-get update && \
    apt-get install -y curl unzip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl https://rclone.org/install.sh | bash

COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

COPY . /usr/src/app

WORKDIR /usr/src/app
CMD ["python", "-u", "sync-driver.py"]
