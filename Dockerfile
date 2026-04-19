# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Final production image
FROM python:3.11-slim

WORKDIR /app

# Create a non-root user for security
RUN groupadd -r nexus && useradd -r -g nexus nexus

# Copy installed dependencies from builder
COPY --from=builder /root/.local /home/nexus/.local
ENV PATH=/home/nexus/.local/bin:$PATH

# Copy application code
COPY app/ ./app/
COPY frontend/ ./frontend/
COPY config/ ./config/
COPY run.py .

# Fix permissions
RUN chown -R nexus:nexus /app
USER nexus

# Expose port (Documentation only, Render uses $PORT)
EXPOSE 8000

# Run the application with production-optimized settings
# We reduce workers to 1 for debugging purposes to ensure tracebacks are logged clearly.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --proxy-headers --forwarded-allow-ips "*"
