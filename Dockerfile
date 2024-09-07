FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE api.settings.prod
ENV PATH $PATH:/root/google-cloud-sdk/bin

WORKDIR /api

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /api/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /api

CMD python manage.py runserver 0.0.0.0:$PORT --settings=api.settings.prod