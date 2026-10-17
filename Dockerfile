FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FORWARDED_ALLOW_IPS="*"

WORKDIR /srv

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 10000

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --proxy-headers"]