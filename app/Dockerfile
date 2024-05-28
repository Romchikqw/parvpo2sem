FROM python:3.12

WORKDIR /app

COPY app/ .

RUN pip install flask

RUN pip install redis

RUN pip install flask-sqlalchemy

CMD ["python3", "app.py"]