FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY ai_module/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN CERTIFI_PATH=$(python -m certifi) && \
    curl -fsSLk "https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt" >> "$CERTIFI_PATH" && \
    printf '\n' >> "$CERTIFI_PATH"

COPY ai_module ./ai_module

EXPOSE 8000

CMD ["python", "-m", "ai_module.app.run_server", "--host", "0.0.0.0", "--port", "8000"]
