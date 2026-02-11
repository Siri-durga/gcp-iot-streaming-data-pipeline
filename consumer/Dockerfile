FROM python:3.9-slim-buster

LABEL maintainer="siri-durga"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Expose port (metadata only)
EXPOSE 8080

CMD ["python", "app.py"]
