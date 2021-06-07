FROM python:slim
WORKDIR /django

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .