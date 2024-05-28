FROM python:3.12

WORKDIR /app

COPY consumer/consumer.py .

RUN pip install flask

RUN pip install redis


CMD ["python3", "consumer.py"]