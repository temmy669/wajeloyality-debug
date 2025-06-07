#!/usr/bin/env bash
set -o errexit

# Install system dependencies for wkhtmltopdf
apt-get update && apt-get install -y wkhtmltopdf

# Install Python dependencies
pip install -r requirements.txt

# Collect static files and run migrations
python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py migrate