FROM python:3.12-slim

# Install system-level dependencies including Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Apply database migrations and start gunicorn
CMD sh -c "python manage.py makemigrations && python manage.py migrate && gunicorn config.wsgi:application"