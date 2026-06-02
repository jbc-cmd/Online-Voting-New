#!/usr/bin/env bash
# exit on error
set -o errexit

# Navigate to the script's directory
cd "$(dirname "$0")"


# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create cache table for rate limiting
python manage.py createcachetable

# Collect static files
python manage.py collectstatic --noinput
