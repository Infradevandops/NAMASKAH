FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY error_handlers.py .
COPY pricing_config.py .
COPY retry_mechanisms.py .
COPY carrier_utils.py .
COPY receipt_system.py .
COPY email_service.py .
COPY static/ ./static/
COPY templates/ ./templates/
COPY services_categorized.json .

EXPOSE 8000

CMD ["python", "main.py"]
