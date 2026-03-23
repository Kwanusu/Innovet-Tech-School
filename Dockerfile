# Backend Dockerfile

# Use a slim, supported Python image
FROM python:3.13-slim-bullseye

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for caching
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Use a non-root user
RUN useradd -m appuser
USER appuser

# Expose Django port
EXPOSE 8000

# Run the Django server (adjust for production w/ gunicorn)
CMD ["gunicorn", "innovet.wsgi:application", "--bind", "0.0.0.0:8000"]