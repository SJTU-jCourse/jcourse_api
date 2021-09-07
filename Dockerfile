FROM python:slim
WORKDIR /django

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt -i https://mirrors.sjtug.sjtu.edu.cn/pypi/web/simple
COPY . .