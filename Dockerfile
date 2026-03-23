FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY src/agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/agent/ .

EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "main.py"]
