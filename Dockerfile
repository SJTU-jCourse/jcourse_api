FROM python:3.13-slim
WORKDIR /django

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt -i https://mirror.sjtu.edu.cn/pypi/web/simple
COPY . .
