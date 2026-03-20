FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# cert.pem and key.pem are generated once during vagrant up and copied here
COPY cert.pem key.pem /app/
COPY app.py .

EXPOSE 443

CMD ["gunicorn", "--bind", "0.0.0.0:443", "--workers", "1", "--access-logfile", "-", \
     "--certfile", "/app/cert.pem", "--keyfile", "/app/key.pem", "app:app"]
