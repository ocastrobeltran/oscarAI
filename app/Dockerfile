FROM python:3.13-alpine

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy all application files (api.py, storage.py, search.py, main.py, etc.)
COPY . /app/

ENV APP_NAME="Oscar AI"
ENV APP_ENV="local"
ENV APP_PORT="8080"
# Add / to PYTHONPATH to allow imports like "from app.storage import ..."
ENV PYTHONPATH=/

EXPOSE 8080

CMD ["python", "/app/main.py"]
