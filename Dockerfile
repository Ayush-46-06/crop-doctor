# Base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_FILE_WATCHER_TYPE=none

WORKDIR /app

# Install curl for container health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install python dependencies with pip cache enabled for fast rebuilds
COPY requirements.txt /app/
RUN pip install --no-cache-dir --default-timeout=120 -r requirements.txt

# Copy source code
COPY . /app/

# Fix line endings (if created on Windows) and set execute permissions
RUN sed -i 's/\r$//' /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Expose Streamlit UI port (8501) and Django API port (8000)
EXPOSE 8501 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["all"]
