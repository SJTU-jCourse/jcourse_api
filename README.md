# jCourse_api: jCourse 的后端
本项目需要与 [jCourse](https://github.com/dujiajun/jcourse) 前端配合使用。

## 开始使用

1. 安装Python, Memcached 和 PostgreSQL 
2. 安装依赖
```shell
pip install -r requirements.txt
```
3. 配置环境变量
```shell
export POSTGRE_PASSWORD=
export POSTGRE_HOST=
export JACCOUNT_CLIENT_ID=
export JACCOUNT_CLIENT_SECRET=
```
4. 初始化数据库
```shell
python manage.py migrate
python manage.py createsuperuser
```
5. 运行单元测试
```shell
python manage.py test
```
7. 运行服务器（仅用于开发测试）
```shell
python manage.py runserver
```

## 使用docker compose
参考 `docker-compose.yml` 如下
```yaml
version: '3'
services:
    backend:
        build: ./django # 替换为 jcourse_api 实际文件夹
        image: jcourse_api:1.0
        command: gunicorn jcourse.wsgi --bind 0.0.0.0:8000
        ports:
            - 8000:8000
        environment:
            HASH_SALT: 
            SECRET_KEY: 
            POSTGRES_PASSWORD: jcourse
            POSTGRES_HOST: db
            REDIS_HOST: cache
            JACCOUNT_CLIENT_ID: 
            JACCOUNT_CLIENT_SECRET: 
            EMAIL_HOST_USER: 
            EMAIL_HOST_PASSWORD: 
            LOGGING_FILE: ./data/django.log
        volumes:
            - ./static:/django/static
            - ./django-data:/django/data
        depends_on:
            - db
            - cache
        restart: always
    db:
        image: postgres:13
        volumes:
            - ./pgdata:/var/lib/postgresql/data
        environment:
            POSTGRES_DB: jcourse
            POSTGRES_USER: jcourse
            POSTGRES_PASSWORD: jcourse
        restart: always
    cache:
        image: redis:latest
        restart: always
```
