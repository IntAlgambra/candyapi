FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/candyapi/candyapi

COPY requirements.txt /usr/src/candyapi

RUN pip install --no-cache-dir -r /usr/src/candyapi/requirements.txt

