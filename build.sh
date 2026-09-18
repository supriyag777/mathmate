#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Tesseract OCR system packages
apt-get update && apt-get install -y tesseract-ocr libtesseract-dev

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py makemigrations
python manage.py migrate