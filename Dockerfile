FROM python:3.10-slim

COPY requirements.txt /app/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update
RUN apt-get install libmagic1 -y
RUN pip install  --upgrade pip
RUN pip install  -r /app/requirements.txt

COPY . /app/

WORKDIR /app/
