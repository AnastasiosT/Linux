FROM python:3.12-slim

WORKDIR /app
COPY agent.py .

EXPOSE 6556

CMD ["python", "agent.py", "--host", "0.0.0.0", "--port", "6556"]
