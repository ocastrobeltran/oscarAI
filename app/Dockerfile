FROM python:3.13-alpine

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY main.py /app/main.py

ENV APP_NAME="Oscar AI"
ENV APP_ENV="local"
ENV APP_PORT="8080"

EXPOSE 8080

CMD ["python", "/app/main.py"]
