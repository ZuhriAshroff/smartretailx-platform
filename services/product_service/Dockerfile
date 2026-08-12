FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY services/product_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY libs ./libs
COPY services/product_service/app ./app

EXPOSE 8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
