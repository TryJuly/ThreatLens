FROM python:3.14-slim

# Les print apparaissent immédiatement dans docker compose logs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common/ common/
COPY sensors/ssh/ sensors/ssh/

RUN useradd --uid 1000 --no-create-home honeypot
USER honeypot

CMD ["python", "-m", "sensors.ssh.ssh_honeypot"]