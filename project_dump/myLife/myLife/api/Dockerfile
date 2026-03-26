# simple Gunicorn-based Dockerfile for the API
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV PORT=8080
CMD ["gunicorn", "app.main:app", "--bind", "0.0.0.0:8080"]
