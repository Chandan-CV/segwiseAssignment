FROM python:3.12

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    chown -R appuser:appgroup /app

COPY . .

RUN chown -R appuser:appgroup /app

# Expose the port for external access
EXPOSE 5000

# Update to bind to all interfaces (0.0.0.0) instead of localhost
CMD ["python", "main.py"]