# Use a lightweight but stable Python base
FROM python:3.10-slim

# Set environment variables for speed and logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies needed for pandas/datareader
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies (use --no-cache-dir to keep image small)
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure the app runs on the port HF expects (7860 for Docker)
EXPOSE 7860

# Correct entrypoint for Streamlit in a container
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
