FROM python:3.14-slim

# Les print apparaissent immédiatement dans docker compose logs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements_enrich.txt .
RUN pip install --no-cache-dir -r requirements_enrich.txt

COPY enrich/ enrich/

RUN useradd --uid 1000 --no-create-home honeypot
USER honeypot

CMD ["python", "-m", "enrich.enrich"]
