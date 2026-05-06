FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY ai_module/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ai_module ./ai_module

EXPOSE 8000

CMD ["python", "-m", "ai_module.app.run_server", "--host", "0.0.0.0", "--port", "8000"]
