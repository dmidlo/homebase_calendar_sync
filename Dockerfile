FROM python:3.12.3-alpine

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apk add --no-cache gcc musl-dev libffi-dev
RUN pip install --upgrade pip
RUN pip install --no-cache-dir homebase_calendar_sync

CMD homebase_calendar_sync